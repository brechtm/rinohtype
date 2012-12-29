
import codecs
import hashlib, time

from binascii import hexlify, unhexlify
from codecs import BOM_UTF16_BE
from collections import OrderedDict
from datetime import datetime
from io import BytesIO, SEEK_END

from . import pdfdoccodec


PDF_VERSION = '1.6'

WHITESPACE = b'\0\t\n\f\r '
DELIMITERS = b'()<>[]{}/%'


def search_function(encoding):
    if encoding == 'pdf_doc':
        return pdfdoccodec.getregentry()


codecs.register(search_function)

# TODO: max line length (not streams)


class Object(object):
    def __init__(self, indirect=False):
        self.indirect = indirect

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self._repr())

    def bytes(self, document):
        if self.indirect:
            reference = document._by_object_id[id(self)]
            out = reference.bytes(document)
        else:
            out = self._bytes(document)
        return out

    def delete(self, document):
        try:
            reference = document._by_object_id[id(self)]
            reference.delete()
        except KeyError:
            pass

    def short_repr(self):
        return repr(self)

    def register_indirect(self, document):
        if self.indirect:
            document.register(self)


class Reference(object):
    def __init__(self, document, identifier, generation):
        self.document = document
        self.identifier = identifier
        self.generation = generation

    def bytes(self, document):
        return '{} {} R'.format(self.identifier,
                                self.generation).encode('utf_8')

    @property
    def target(self):
        return self.document[self.identifier]

    def delete(self, document=None):
        if document == self.document:
            del self.document[self.identifier]

    def __repr__(self):
        return '{}<{} {}>'.format(self.target.__class__.__name__,
                                  self.identifier, self.generation)


class Boolean(Object):
    def __init__(self, value, indirect=False):
        super().__init__(indirect)
        self.value = value

    def _repr(self):
        return self.value

    def _bytes(self, document):
        return b'true' if self.value else b'false'


class Integer(Object, int):
    def __new__(cls, value, base=10, indirect=False):
        try:
            obj = int.__new__(cls, value, base)
        except TypeError:
            obj = int.__new__(cls, value)
        return obj

    def __init__(self, value, base=10, indirect=False):
        Object.__init__(self, indirect)

    def _repr(self):
        return int.__repr__(self)

    def _bytes(self, document):
        return int.__str__(self).encode('utf_8')


class Real(Object, float):
    def __new__(cls, value, indirect=False):
        return float.__new__(cls, value)

    def __init__(self, value, indirect=False):
        Object.__init__(self, indirect)

    def _repr(self):
        return float.__repr__(self)

    def _bytes(self, document):
        return float.__repr__(self).encode('utf_8')


class String(Object, bytes):
    ESCAPED_CHARACTERS = {ord(b'\n'): br'\n',
                          ord(b'\r'): br'\r',
                          ord(b'\t'): br'\t',
                          ord(b'\b'): br'\b',
                          ord(b'\f'): br'\f',
                          ord(b'\\'): br'\\',
                          ord(b'('): br'\(',
                          ord(b')'): br'\)'}

    def __new__(cls, value, indirect=False):
        try:
            value = BOM_UTF16_BE + value.encode('utf_16_be')
        except AttributeError:
            pass
        return bytes.__new__(cls, value)

    def __init__(self, value, indirect=False):
        Object.__init__(self, indirect)

    def __str__(self):
        if self.startswith(BOM_UTF16_BE):
            return self.decode('utf_16')
        else:
            return self.decode('pdf_doc')

    def _repr(self):
        try:
            return "'" + str(self) + "'"
        except UnicodeDecodeError:
            return '<{}{}>'.format(hexlify(self[:10]).decode(),
                                   '...' if len(self) > 10 else '')

    def _bytes(self, document):
        escaped = bytearray()
        for char in self:
            if char in self.ESCAPED_CHARACTERS.keys():
                escaped += ESCAPED_CHARACTERS[char]
            else:
                escaped.append(char)
        return b'(' + escaped + b')'


class HexString(Object, bytes):
    def __new__(cls, value, indirect=False):
        return bytes.__new__(cls, value)

    def __init__(self, byte_string, indirect=False):
        Object.__init__(self, indirect)

    def _repr(self):
        return hexlify(self).decode()

    def _bytes(self, document):
        return b'<' + hexlify(self) + b'>'


class Date(String):
    def __new__(cls, timestamp, indirect=False):
        local_time = datetime.fromtimestamp(timestamp)
        utc_time = datetime.utcfromtimestamp(timestamp)
        utc_offset = local_time - utc_time
        utc_offset_minutes, utc_offset_seconds = divmod(utc_offset.seconds, 60)
        utc_offset_hours, utc_offset_minutes = divmod(utc_offset_minutes, 60)
        string = local_time.strftime('D:%Y%m%d%H%M%S')
        string += "{:+03d}'{:02d}'".format(utc_offset_hours, utc_offset_minutes)
        return String.__new__(cls, string, indirect)


class Name(Object, bytes):
    # TODO: names should be unique (per document), so check
    def __new__(cls, value, indirect=False):
        try:
            value = value.encode('utf_8')
        except AttributeError:
            pass
        return bytes.__new__(cls, value)

    def __init__(self, value, indirect=False):
        Object.__init__(self, indirect)

    def __str__(self):
        return self.decode('utf_8')

    def _repr(self):
        return str(self)

    def _bytes(self, document):
        escaped = bytearray()
        for char in self:
            if char in WHITESPACE + DELIMITERS + b'#':
                escaped += '#{:02x}'.format(char).encode('ascii')
            else:
                escaped.append(char)
        return b'/' + escaped


class Container(Object):
    def __init__(self, indirect=False):
        super().__init__(indirect)

    def register_indirect(self, document):
        register_children = True
        if self.indirect:
            register_children = id(self) not in document._by_object_id
            document.register(self)
        if register_children:
            for item in self.children():
                item.register_indirect(document)


class Array(Container, list):
    # TODO: not all methods of list are overridden, so funny
    # behavior is to be expected
    def __init__(self, items=[], indirect=False):
        Container.__init__(self, indirect)
        list.__init__(self, items)

    def _repr(self):
        return ', '.join(item.short_repr() for item in self)

    def _bytes(self, document):
        return b'[' + b' '.join(elem.bytes(document) for elem in self) + b']'

    def short_repr(self):
        return '<{} {}>'.format(self.__class__.__name__, id(self))

    def children(self):
        for item in self:
            yield item


class Dictionary(Container, OrderedDict):
    def __init__(self, indirect=False):
        Container.__init__(self, indirect)
        OrderedDict.__init__(self)

    def _repr(self):
        return ', '.join('{}: {}'.format(key, value.short_repr())
                         for key, value in self.items())

    def __setitem__(self, key, value):
        super().__setitem__(key if isinstance(key, Name) else Name(key), value)

    def __getitem__(self, key):
        return super().__getitem__(key if isinstance(key, Name) else Name(key))

    def __contains__(self, key):
        return super().__contains__(key if isinstance(key, Name) else Name(key))

    def _bytes(self, document):
        return b'<< ' + b' '.join(key.bytes(document) + b' ' +
                                  value.bytes(document)
                                  for key, value in self.items()) + b' >>'

    def short_repr(self):
        return '<{} {}>'.format(self.__class__.__name__, id(self))

    def children(self):
        for item in self.values():
            yield item


class Stream(Dictionary):
    def __init__(self, filter=None):
        # (Streams are always indirectly referenced)
        super().__init__(indirect=True)
        self.filter = filter
        self.data = BytesIO()

    def _bytes(self, document):
        if self.filter:
            encoded = self.filter.encode(self.data.getvalue())
            self.data = BytesIO(encoded)
            self['Filter'] = Name(self.filter.name)
        if 'Length' in self:
            self['Length'].delete(document)
        self['Length'] = Integer(self.size)
        out = super()._bytes(document)
        out += b'\nstream\n'
        out += self.data.getvalue()
        out += b'\nendstream'
        return out

    def read(self, *args, **kwargs):
        return self.data.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        return self.data.write(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self.data.tell(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.data.seek(*args, **kwargs)

    def getvalue(self):
        return self.data.getvalue()

    @property
    def size(self):
        restore_pos = self.tell()
        self.seek(0, SEEK_END)
        size = self.tell()
        self.seek(restore_pos)
        return size


class XObjectForm(Stream):
    def __init__(self, bounding_box):
        super().__init__()
        self['Type'] = Name('XObject')
        self['Subtype'] = Name('Form')
        self['BBox'] = bounding_box


class Null(Object):
    def __init__(self, indirect=False):
        super().__init__(indirect)

    def __repr__(self):
        return self.__class__.__name__

    def _bytes(self, document):
        return b'null'



class Document(dict):
    def __init__(self):
        self.catalog = Catalog()
        self.info = Dictionary(indirect=True)
        self.timestamp = time.time()
        self.info['CreationDate'] = Date(self.timestamp)
        self.id = None
        self._by_object_id = {}

    def register(self, obj):
        if id(obj) not in self._by_object_id:
            identifier, generation = self.max_identifier + 1, 0
            reference = Reference(self, identifier, generation)
            self._by_object_id[id(obj)] = reference
            self[identifier] = obj

    @property
    def max_identifier(self):
        try:
            identifier = max(self.keys())
        except ValueError:
            identifier = 0
        return identifier

    def _write_xref_table(self, file, addresses):
        def out(string):
            file.write(string + b'\n')

        out(b'xref')
        out('0 {}'.format(self.max_identifier + 1).encode('utf_8'))
        out(b'0000000000 65535 f ')
        last_free = 0
        for identifier in range(1, self.max_identifier + 1):
            try:
                address = addresses[identifier]
                out('{:010d} {:05d} n '.format(address, 0).encode('utf_8'))
            except KeyError:
                out(b'0000000000 65535 f ')
                last_free = identifier

    def write(self, file_or_filename):
        def out(string):
            file.write(string + b'\n')

        try:
            file = open(file_or_filename, 'wb')
            close_file = True
        except TypeError:
            file = file_or_filename
            close_file = False

        self.catalog.register_indirect(self)
        self.info.register_indirect(self)
        if 'Producer' in self.info:
            self.info['Producer'].delete(self)
        if 'ModDate' in self.info:
            self.info['ModDate'].delete(self)
        self.info['Producer'] = String('pyte PDF backend')
        self.info['ModDate'] = Date(self.timestamp)

        out('%PDF-{}'.format(PDF_VERSION).encode('utf_8'))
        file.write(b'%\xDC\xE1\xD8\xB7\n')
        addresses = {}
        for identifier in range(1, self.max_identifier + 1):
            if identifier in self:
                obj = self[identifier]
                addresses[identifier] = file.tell()
                out('{} 0 obj'.format(identifier).encode('utf_8'))
                out(obj._bytes(self))
                out(b'endobj')
        xref_table_address = file.tell()
        self._write_xref_table(file, addresses)
        out(b'trailer')
        trailer = Dictionary()
        trailer['Size'] = Integer(self.max_identifier + 1)
        trailer['Root'] = self.catalog
        trailer['Info'] = self.info
        md5sum = hashlib.md5()
        md5sum.update(str(self.timestamp).encode())
        md5sum.update(str(file.tell()).encode())
        for value in self.info.values():
            md5sum.update(value._bytes(self))
        new_id = HexString(md5sum.digest())
        if self.id:
            self.id[1] = new_id
        else:
            self.id = Array([new_id, new_id])
        trailer['ID'] = self.id
        out(trailer.bytes(self))
        out(b'startxref')
        out(str(xref_table_address).encode('utf_8'))
        out(b'%%EOF')
        if close_file:
            file.close()


class Catalog(Dictionary):
    def __init__(self):
        super().__init__(indirect=True)
        self['Type'] = Name('Catalog')
        self['Pages'] = Pages()


class Pages(Dictionary):
    def __init__(self):
        super().__init__(indirect=True)
        self['Type'] = Name('Pages')
        self['Count'] = Integer(0)
        self['Kids'] = Array()

    def new_page(self, width, height):
        page = Page(self, width, height)
        self['Kids'].append(page)
        self['Count'] = Integer(self['Count'] + 1)
        return page


class Page(Dictionary):
    def __init__(self, parent, width, height):
        super().__init__(indirect=True)
        self['Type'] = Name('Page')
        self['Parent'] = parent
        self['Resources'] = Dictionary()
        self['MediaBox'] = Array([Integer(0), Integer(0),
                                  Real(width), Real(height)])

    def to_xobject_form(self):
        content_stream = self['Contents']
        xobject = XObjectForm(self['MediaBox'])
        if 'Filter' in content_stream:
            xobject['Filter'] = content_stream['Filter']
        if 'Resources' in self:
            xobject['Resources'] = self['Resources']
        xobject.write(content_stream.getvalue())
        return xobject


class Font(Dictionary):
    def __init__(self, indirect):
        super().__init__(indirect)
        self['Type'] = Name('Font')


class SimpleFont(Font):
    def __init__(self):
        raise NotImplementedError()


class Type1Font(Font):
    def __init__(self, font, encoding, font_descriptor):
        super().__init__(True)
        self.font = font
        self['Subtype'] = Name('Type1')
        self['BaseFont'] = Name(font.name)
        self['Encoding'] = encoding
        self['FontDescriptor'] = font_descriptor

    def _bytes(self, document):
        widths = []
        by_code = {glyph.code: glyph
                   for glyph in self.font.metrics._glyphs.values()
                   if glyph.code >= 0}
        try:
            enc_differences = self['Encoding']['Differences']
            first, last = min(enc_differences.taken), max(enc_differences.taken)
        except KeyError:
            first, last = min(by_code.keys()), max(by_code.keys())
        self['FirstChar'] = Integer(first)
        self['LastChar'] = Integer(last)
        for code in range(first, last + 1):
            try:
                glyph = by_code[code]
                width = glyph.width
            except KeyError:
                try:
                    glyph = enc_differences.by_code[code]
                    width = glyph.width
                except (KeyError, NameError):
                    width = 0
            widths.append(width)
        self['Widths'] = Array(map(Real, widths))
        return super()._bytes(document)


class CompositeFont(Font):
    def __init__(self, descendant_font, encoding, to_unicode=None):
        super().__init__(True)
        self['Subtype'] = Name('Type0')
        self['BaseFont'] = descendant_font.composite_font_name(encoding)
        self['DescendantFonts'] = Array([descendant_font], False)
        try:
            self['Encoding'] = Name(encoding)
        except NotImplementedError:
            self['Encoding'] = encoding
        if to_unicode:
            self['ToUnicode'] = to_unicode


class CIDSystemInfo(Dictionary):
    def __init__(self, ordering, registry, supplement):
        super().__init__(False)
        self['Ordering'] = String(ordering)
        self['Registry'] = String(registry)
        self['Supplement'] = Integer(supplement)


class CIDFont(Font):
    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None):
        super().__init__(True)
        self['BaseFont'] = Name(base_font)
        self['FontDescriptor'] = font_descriptor
        self['CIDSystemInfo'] = cid_system_info
        self['DW'] = Integer(dw)
        if w:
            self['W'] = w

    def composite_font_name(self, encoding):
        raise NotImplementedError()


class CIDFontType0(CIDFont):
    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None):
        super().__init__(base_font, cid_system_info, font_descriptor, dw, w)
        self['Subtype'] = Name('CIDFontType0')

    def composite_font_name(self, encoding):
        try:
            suffix = encoding['CMapName']
        except TypeError:
            suffix = encoding
        return Name('{}-{}'.format(self['BaseFont'], suffix))


class CIDFontType2(CIDFont):
    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None, cid_to_gid_map=None):
        super().__init__(base_font, cid_system_info, font_descriptor, dw, w)
        self['Subtype'] = Name('CIDFontType2')
        if cid_to_gid_map:
            self['CIDToGIDMap'] = cid_to_gid_map

    def composite_font_name(self, encoding):
        return self['BaseFont']


class FontDescriptor(Dictionary):
    def __init__(self, font_name, flags, font_bbox, italic_angle, ascent,
                 descent, cap_height, stem_v, font_file, x_height=0):
        super().__init__(True)
        self['Type'] = Name('FontDescriptor')
        self['FontName'] = Name(font_name)
        self['Flags'] = Integer(flags)
        self['FontBBox'] = Array([Integer(item) for item in font_bbox])
        self['ItalicAngle'] = Integer(italic_angle)
        self['Ascent'] = Integer(ascent)
        self['Descent'] = Integer(descent)
        self['CapHeight'] = Integer(cap_height)
        self['XHeight'] = Integer(x_height)
        self['StemV'] = Integer(stem_v)
        self[font_file.key] = font_file


class Type3FontDescriptor(FontDescriptor):
    def __init__(self):
        raise NotImplementedError()


class Type1FontFile(Stream):
    key = 'FontFile'

    def __init__(self, header, body, filter=None):
        super().__init__(filter)
        self['Length1'] = Integer(len(header))
        self['Length2'] = Integer(len(body))
        self['Length3'] = Integer(0)
        self.write(header)
        self.write(body)


class OpenTypeFontFile(Stream):
    key = 'FontFile3'

    def __init__(self, font_data, filter=None):
        super().__init__(filter)
        self['Subtype'] = Name('OpenType')
        self.write(font_data)


class FontEncoding(Dictionary):
    def __init__(self, indirect=True):
        super().__init__(indirect)
        self['Type'] = Name('Encoding')


class EncodingDifferences(Object):
    def __init__(self, taken):
        super().__init__(False)
        self.taken = taken
        self.previous_free = 1
        self.by_glyph = {}
        self.by_code = {}

    def register(self, glyph):
        try:
            code = self.by_glyph[glyph]
        except KeyError:
            while self.previous_free in self.taken:
                self.previous_free += 1
                if self.previous_free > 255:
                    raise NotImplementedError('Encoding vector is full')
            code = self.previous_free
            self.taken.append(code)
            self.by_glyph[glyph] = code
            self.by_code[code] = glyph
        return code

    def _bytes(self, document):
        output = b'['
        previous = 256
        for code in sorted(self.by_code.keys()):
            if code != previous + 1:
                output += b' ' + Integer(code)._bytes(document)
            output += b' ' + Name(self.by_code[code].name)._bytes(document)
        output += b' ]'
        return output
