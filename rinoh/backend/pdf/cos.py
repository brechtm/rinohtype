# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import codecs
import hashlib, time

from binascii import hexlify
from codecs import BOM_UTF16_BE
from contextlib import contextmanager
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from io import BytesIO, SEEK_END

from . import pdfdoccodec
from ... import __version__, __release_date__

PDF_VERSION = '1.6'

WHITESPACE = b'\0\t\n\f\r '
DELIMITERS = b'()<>[]{}/%'


# TODO: max line length (not streams)


class Object(object):
    PREFIX = b''
    POSTFIX = b''

    def __init__(self, indirect=False):
        self.indirect = indirect

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self._repr())

    @property
    def object(self):
        return self

    def bytes(self, document):
        if self.indirect:
            reference = document._by_object_id[id(self)]
            out = reference.bytes(document)
        else:
            out = self.direct_bytes(document)
        return out

    def direct_bytes(self, document):
        return self.PREFIX + self._bytes(document) + self.POSTFIX

    def delete(self, document):
        try:
            reference = document._by_object_id[id(self)]
            reference.delete()
        except KeyError:
            pass

    def short_repr(self):
        return repr(self)

    def register_indirect(self, document, visited=None):
        if self.indirect and id(self) not in visited:
            document.register(self)


class Reference(object):
    def __init__(self, document, identifier, generation):
        self.document = document
        self.identifier = identifier
        self.generation = generation

    @property
    def object(self):
        return self.document[self.identifier]

    def bytes(self, document):
        return '{} {} R'.format(self.identifier,
                                self.generation).encode('utf_8')

    def delete(self, document=None):
        if document == self.document:
            del self.document[self.identifier]

    def __repr__(self):
        return '{}<{} {}>'.format(self.object.__class__.__name__,
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
    PREFIX = b'('
    POSTFIX = b')'
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
            value = value.encode('pdf_doc')
        except UnicodeEncodeError:
            value = BOM_UTF16_BE + value.encode('utf_16')
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
            if char in self.ESCAPED_CHARACTERS:
                escaped += self.ESCAPED_CHARACTERS[char]
            else:
                escaped.append(char)
        return escaped


class HexString(Object, bytes):
    PREFIX = b'<'
    POSTFIX = b'>'

    def __new__(cls, value, indirect=False):
        return bytes.__new__(cls, value)

    def __init__(self, byte_string, indirect=False):
        Object.__init__(self, indirect)

    def _repr(self):
        return hexlify(self).decode()

    def _bytes(self, document):
        return hexlify(self)


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
    PREFIX = b'/'

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
        return escaped


class Container(Object):
    def __init__(self, indirect=False):
        super().__init__(indirect)

    def register_indirect(self, document, visited=None):
        if visited is None:     # visited helps prevent infinite looping when
            visited = set()     # an object holds a reference to an ancestor
        if id(self) not in visited:
            if self.indirect:
                document.register(self)
                visited.add(id(self))
            for item in self.children():
                item.register_indirect(document, visited)


class Array(Container, list):
    PREFIX = b'['
    POSTFIX = b']'

    # TODO: not all methods of list are overridden, so funny
    # behavior is to be expected
    def __init__(self, items=[], indirect=False):
        Container.__init__(self, indirect)
        list.__init__(self, items)

    def __getitem__(self, arg):
        if isinstance(arg, slice):
            items = [elem.object for elem in super().__getitem__(arg)]
            return self.__class__(items, indirect=self.indirect)
        else:
            return super().__getitem__(arg).object

    def _repr(self):
        return ', '.join(elem.object.short_repr() for elem in self)

    def _bytes(self, document):
        return b' '.join(elem.bytes(document) for elem in self)

    def short_repr(self):
        return '<{} {}>'.format(self.__class__.__name__, id(self))

    def children(self):
        for item in self:
            yield item.object


def convert_key_to_name(method):
    @wraps(method)
    def wrapper(obj, key, *args, **kwargs):
        if not isinstance(key, Name):
            key = Name(key)
        return method(obj, key, *args, **kwargs)
    return wrapper


class Dictionary(Container, OrderedDict):
    PREFIX = b'<<'
    POSTFIX = b'>>'

    type = None
    subtype = None

    def __init__(self, indirect=False, **items):
        Container.__init__(self, indirect)
        OrderedDict.__init__(self, **items)
        if self.__class__.type:
            self['Type'] = Name(self.__class__.type)
        if self.__class__.subtype:
            self['Subtype'] = Name(self.__class__.subtype)

    def _repr(self):
        return ', '.join('{}: {}'.format(key, value.object.short_repr())
                         for key, value in self.items())

    @convert_key_to_name
    def __getitem__(self, key):
        return super().__getitem__(key).object

    __setitem__ = convert_key_to_name(OrderedDict.__setitem__)

    __contains__ = convert_key_to_name(OrderedDict.__contains__)

    get = convert_key_to_name(OrderedDict.get)

    def _bytes(self, document):
        return b' '.join(key.bytes(document) + b' ' + value.bytes(document)
                         for key, value in self.items())

    def short_repr(self):
        return '<{} {}>'.format(self.__class__.__name__, id(self))

    def children(self):
        for item in self.values():
            yield item.object


from .filter import PassThrough


class Stream(Dictionary):
    def __init__(self, filter=None):
        # (Streams are always indirectly referenced)
        self._data = BytesIO()
        self._filter = filter or PassThrough()
        super().__init__(indirect=True)
        self._coder = None

    def direct_bytes(self, document):
        out = bytearray()
        try:
            self._coder.close()
        except AttributeError:
            pass
        if not isinstance(self._filter, PassThrough):
            self['Filter'] = Name(self._filter.name)
            if self._filter.params:
                self['DecodeParms'] = self._filter.params
        if 'Length' in self:
            self['Length'].delete(document)
        self['Length'] = Integer(self._data.tell())
        out += super().direct_bytes(document)
        out += b'\nstream\n'
        out += self._data.getvalue()
        out += b'\nendstream'
        return out

    def read(self, n=-1):
        try:
            return self._coder.read(n)
        except AttributeError:
            self._data.seek(0)
            self._coder = self._filter.decoder(self._data)
            return self.read(n)

    def write(self, b):
        try:
            return self._coder.write(b)
        except AttributeError:
            self._data.seek(0)
            self._coder = self._filter.encoder(self._data)
            return self.write(b)

    def reset(self):
        self._coder = None

    def __getattr__(self, name):
        # almost as good as inheriting from BytesIO (which is not possible)
        return getattr(self._data, name)


class XObjectForm(Stream):
    type = 'XObject'
    subtype = 'Form'

    def __init__(self, bounding_box):
        super().__init__()
        self['BBox'] = bounding_box


class ObjectStream(Stream):
    type = 'ObjStm'

    def get_object(self, document, index):
        try:
            object_reader = self._object_reader
            offsets = self._offsets
        except AttributeError:
            decompressed_data = BytesIO(self.read())
            from .reader import PDFObjectReader
            object_reader = PDFObjectReader(decompressed_data, document)
            offsets = self._offsets = {}
            for i in range(self['N']):
                object_number = int(object_reader.read_number())
                offset = int(self['First'] + object_reader.read_number())
                offsets[i] = offset
            self._object_reader = object_reader
        object_reader.file.seek(offsets[index])
        return object_reader.next_item(indirect=True)


class Null(Object):
    def __init__(self, indirect=False):
        super().__init__(indirect)

    def __repr__(self):
        return self.__class__.__name__

    def _bytes(self, document):
        return b'null'



class Document(dict):
    PRODUCER = 'RinohType v{} PDF backend ({})'.format(__version__,
                                                       __release_date__)

    def __init__(self, creator):
        self.catalog = Catalog()
        self.info = Dictionary(indirect=True)
        self.timestamp = time.time()
        self.set_info('Creator', creator)
        self.set_info('Producer', self.PRODUCER)
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
        for identifier in range(1, self.max_identifier + 1):
            try:
                address = addresses[identifier]
                out('{:010d} {:05d} n '.format(address, 0).encode('utf_8'))
            except KeyError:
                out(b'0000000000 65535 f ')

    def set_info(self, field, string):
        assert field in ('Creator', 'Producer',
                         'Title', 'Author', 'Subject', 'Keywords')
        if string:
            if field in self.info:
                self.info[field].delete(self)
            self.info[field] = String(string)

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
        if 'ModDate' in self.info:
            self.info['ModDate'].delete(self)
        self.info['ModDate'] = Date(self.timestamp)

        out('%PDF-{}'.format(PDF_VERSION).encode('utf_8'))
        file.write(b'%\xDC\xE1\xD8\xB7\n')
        # write out indirect objects
        addresses = {}
        for identifier in range(1, self.max_identifier + 1):
            if identifier in self:
                obj = self[identifier]
                addresses[identifier] = file.tell()
                out('{} 0 obj'.format(identifier).encode('utf_8'))
                out(obj.direct_bytes(self))
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
    type = 'Catalog'

    def __init__(self):
        super().__init__(indirect=True)
        self['Pages'] = Pages()


class Pages(Dictionary):
    type = 'Pages'

    def __init__(self):
        super().__init__(indirect=True)
        self['Count'] = Integer(0)
        self['Kids'] = Array()

    def new_page(self, width, height):
        page = Page(self, width, height)
        self['Kids'].append(page)
        self['Count'] = Integer(self['Count'] + 1)
        return page


class Page(Dictionary):
    type = 'Page'

    def __init__(self, parent, width, height):
        super().__init__(indirect=True)
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


class Rectangle(Array):
    def __init__(self, left, bottom, right, top, indirect=False):
        super().__init__([Real(value) for value in (left, bottom, right, top)],
                         indirect)


# interactivity

class Action(Dictionary):
    type = 'Action'
    action_type = None

    def __init__(self, next=None, indirect=False):
        super().__init__(indirect)
        if self.__class__.action_type:
            self['S'] = Name(self.__class__.action_type)
        if next:
            self['Next'] = next


class Destination(Dictionary):
    pass


class URIAction(Action):
    action_type = 'URI'

    def __init__(self, uri, is_map=False, next=None, indirect=False):
        super().__init__(next, indirect)
        self['URI'] = String(uri)
        self['IsMap'] = Boolean(is_map)


class Annotation(Dictionary):
    type = 'Annot'

    def __init__(self, rectangle, indirect=False):
        super().__init__(indirect)
        self['Rect'] = rectangle
        self['Border'] = Array(3 * [Integer(0)])


class LinkAnnotation(Annotation):
    subtype = 'Link'

    def __init__(self, rectangle, action=None, destination=None,
                 indirect=False):
        super().__init__(rectangle, indirect)
        assert (action and destination) is None
        if action:
            self['A'] = action
        if destination:
            self['Dest'] = destination


# fonts

class Font(Dictionary):
    type = 'Font'


class SimpleFont(Font):
    def __init__(self):
        raise NotImplementedError()


class Type1Font(Font):
    subtype = 'Type1'

    def __init__(self, font, encoding, font_descriptor):
        super().__init__(True)
        self.font = font
        self['BaseFont'] = Name(font.name)
        self['Encoding'] = encoding
        self['FontDescriptor'] = font_descriptor

    def _bytes(self, document):
        if not 'Widths' in self:
            widths = []
            by_code = {glyph.code: glyph
                       for glyph in self.font._glyphs.values()
                       if glyph.code >= 0}
            try:
                differences = self['Encoding']['Differences']
                first, last = min(differences.taken), max(differences.taken)
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
                        glyph = differences.by_code[code]
                        width = glyph.width
                    except (KeyError, NameError):
                        width = 0
                widths.append(width)
            self['Widths'] = Array(map(Real, widths))
        return super()._bytes(document)


class CompositeFont(Font):
    subtype = 'Type0'

    def __init__(self, descendant_font, encoding, to_unicode=None):
        super().__init__(True)
        self['BaseFont'] = descendant_font.composite_font_name(encoding)
        self['DescendantFonts'] = Array([descendant_font], False)
        try:
            self['Encoding'] = Name(encoding)
        except NotImplementedError:
            self['Encoding'] = encoding
        if to_unicode is not None:
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
    subtype = 'CIDFontType0'

    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None):
        super().__init__(base_font, cid_system_info, font_descriptor, dw, w)

    def composite_font_name(self, encoding):
        try:
            suffix = encoding['CMapName']
        except TypeError:
            suffix = encoding
        return Name('{}-{}'.format(self['BaseFont'], suffix))


class CIDFontType2(CIDFont):
    subtype = 'CIDFontType2'

    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None, cid_to_gid_map=None):
        super().__init__(base_font, cid_system_info, font_descriptor, dw, w)
        if cid_to_gid_map:
            self['CIDToGIDMap'] = cid_to_gid_map

    def composite_font_name(self, encoding):
        return self['BaseFont']


class FontDescriptor(Dictionary):
    type = 'FontDescriptor'

    def __init__(self, font_name, flags, font_bbox, italic_angle, ascent,
                 descent, cap_height, stem_v, font_file, x_height=0):
        super().__init__(True)
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
        # TODO: subclass Array
        output = b'['
        previous = 256
        for code in sorted(self.by_code.keys()):
            if code != previous + 1:
                output += b' ' + Integer(code).bytes(document)
            output += b' ' + Name(self.by_code[code].name).bytes(document)
            previous = code
        output += b' ]'
        return output


class ToUnicode(Stream):
    def __init__(self, mapping, filter=None):
        super().__init__(filter=filter)
        with self._begin_resource('/CIDInit /ProcSet findresource'):
            with self._begin_resource('12 dict'):
                with self._begin('cmap'):
                    cid_system_info = Dictionary()
                    cid_system_info['Registry'] = String('Adobe')
                    cid_system_info['Ordering'] = String('UCS')
                    cid_system_info['Supplement'] = Integer('0')
                    self._def('CIDSystemInfo', cid_system_info)
                    self._def('CMapName', Name('Adobe-Identity-UCS'))
                    self._def('CMapType', Integer(2))
                    with self._begin('codespacerange', 1):
                        self._value(0x0000)
                        self._value(0xFFFF)
                        self.write(b'\n')
                    #with self._begin('bfrange', 1):
                    #    # TODO: limit to sets of 100 entries
                    #    # TODO: ranges should not cross first-byte limits
                    #    self._value(0x0000)
                    #    self._value(0xFFFF)
                    #    self._value(0x0000)
                    with self._begin('bfchar', len(mapping)):
                        # TODO: limit to sets of 100 entries
                        for unicode, cid in mapping.items():
                            self._value(cid)
                            self._value(unicode)
                            self.write(b'\n')
                self.print('CMapName currentdict /CMap defineresource pop')

    @contextmanager
    def _begin_resource(self, string):
        self.print('{} begin'.format(string))
        yield
        self.print('end')

    @contextmanager
    def _begin(self, string, length=None):
        if length:
            self.print('{} '.format(length), end='')
        self.print('begin{}'.format(string))
        yield
        self.print('end{}'.format(string))

    def _def(self, key, value):
        self.print('/{} '.format(key), end='')
        self.write(value.bytes(None))
        self.print(' def')

    def _value(self, value, number_of_bytes=2):
        hex_str = HexString((value).to_bytes(number_of_bytes, byteorder='big'))
        self.write(hex_str.bytes(None))

    def print(self, strng, end='\n'):
        self.write(strng.encode('ascii'))
        self.write(end.encode('ascii'))
