# This file is part of rinohtype, the Python document preparation system.
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
from itertools import chain

from ... import __version__, __release_date__

from . import pdfdoccodec

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

    def _bytes(self, document):
        raise NotImplementedError

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


class Null(Object):
    def __init__(self, indirect=False):
        super().__init__(indirect)

    def __repr__(self):
        return self.__class__.__name__

    def __bool__(self):
        return False

    def _bytes(self, document):
        return b'null'


class Reference(object):
    def __init__(self, document, identifier, generation):
        self.document = document
        self.identifier = identifier
        self.generation = generation

    @property
    def object(self):
        return self.document[self.identifier]

    def bytes(self, document):
        if document is self.document:
            identifier, generation = self.identifier, self.generation
        else:
            obj = self.document[self.identifier]
            reference = document.register(obj)
            identifier, generation = reference.identifier, reference.generation
        return '{} {} R'.format(identifier, generation).encode('utf_8')

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

    def __bool__(self):
        return self.value

    def __eq__(self, other):
        return self.value == other.value

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
        return self._repr().encode('utf_8')


class Real(Object, float):
    def __new__(cls, value, indirect=False):
        return float.__new__(cls, value)

    def __init__(self, value, indirect=False):
        Object.__init__(self, indirect)

    def _repr(self):
        return float.__repr__(self)

    def _bytes(self, document):
        return '{:.8f}'.format(self).rstrip('0').rstrip('.').encode('utf_8')


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
            assert isinstance(value, bytes)
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

    def __init__(self, *args, indirect=False, **items):
        Container.__init__(self, indirect)
        OrderedDict.__init__(self, *args, **items)
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

    __delitem__ = convert_key_to_name(OrderedDict.__delitem__)

    __contains__ = convert_key_to_name(OrderedDict.__contains__)

    get = convert_key_to_name(OrderedDict.get)

    setdefault = convert_key_to_name(OrderedDict.setdefault)    # PyPy

    def _bytes(self, document):
        return b' '.join(key.bytes(document) + b' ' + value.bytes(document)
                         for key, value in self.items())

    def short_repr(self):
        return '<{} {}>'.format(self.__class__.__name__, id(self))

    def children(self):
        for item in self.values():
            yield item.object


from .filter import PassThrough, FilterPipeline


class Stream(Dictionary):
    def __init__(self, filter=None, **items):
        # (Streams are always indirectly referenced)
        self._data = BytesIO()
        try:
            self.filter = FilterPipeline(filter)
        except TypeError:
            self.filter = filter or PassThrough()
        super().__init__(indirect=True, **items)
        self._coder = None

    def direct_bytes(self, document):
        out = bytearray()
        self.reset()
        if not isinstance(self.filter, PassThrough):
            self['Filter'] = self.filter.name
            if self.filter.params:
                self['DecodeParms'] = self.filter.params
        if 'Length' in self:
            self['Length'].delete(document)
        assert self._data.tell() == self._data.seek(0, SEEK_END)
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
            self._coder = self.filter.decoder(self._data)
            return self.read(n)

    def write(self, b, **kwargs):
        try:
            return self._coder.write(b)
        except AttributeError:
            self._data.seek(0)
            self._coder = self.filter.encoder(self._data, **kwargs)
            return self.write(b)

    def write_raw(self, b):
        return self._data.write(b)

    def reset(self):
        if self._coder:
            self._coder.close()
            self._coder = None

    def __getattr__(self, name):
        # almost as good as inheriting from BytesIO (which is not possible)
        return getattr(self._data, name)


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



class Document(dict):
    PRODUCER = 'rinohtype v{} PDF backend ({})'.format(__version__,
                                                       __release_date__)

    def __init__(self, creator,
                 title=None, author=None, subject=None, keywords=None):
        self.catalog = Catalog()
        self.catalog['PageLabels'] = Dictionary(indirect=True)
        self.catalog['PageLabels']['Nums'] = Array()
        self.info = Dictionary(indirect=True)
        self.timestamp = time.time()
        self.set_info('Creator', creator)
        self.set_info('Producer', self.PRODUCER)
        self.set_info('Title', title)
        self.set_info('Author', author)
        self.set_info('Subject', subject)
        self.set_info('Keywords', keywords)
        self.info['CreationDate'] = Date(self.timestamp)
        self.id = None
        self.dests = {}
        self._by_object_id = {}

    def get_page(self, index):
        for i, page in enumerate(self.catalog['Pages'].pages):
            if i == index:
                return page
        raise IndexError

    def register(self, obj):
        try:
            reference = self._by_object_id[id(obj)]
        except KeyError:
            identifier, generation = self.max_identifier + 1, 0
            reference = Reference(self, identifier, generation)
            self._by_object_id[id(obj)] = reference
            self[identifier] = obj
        return reference

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

    def build_dests_names_array(self):
        if 'Names' in self.catalog:
            self.catalog['Names'].delete(self)
        names = self.catalog['Names'] = Dictionary(indirect=True)
        dests = names['Dests'] = Dictionary(indirect=True)
        dests_names = dests['Names'] = Array()
        for name in sorted(self.dests):
            dests_names.append(name)
            dests_names.append(self.dests[name])

    def write(self, file_or_filename):
        def out(string):
            file.write(string + b'\n')

        try:
            file = open(file_or_filename, 'wb')
            close_file = True
        except TypeError:
            file = file_or_filename
            close_file = False

        self.build_dests_names_array()
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


class XRefStream(Stream):
    type = 'XRef'


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

    @property
    def pages(self):
        for kid in self['Kids']:
            yield from kid.object.pages


class Page(Dictionary):
    type = 'Page'

    def __init__(self, parent, width, height):
        super().__init__(indirect=True)
        self['Parent'] = parent
        self['Resources'] = Dictionary()
        self['MediaBox'] = Array([Integer(0), Integer(0),
                                  Real(width), Real(height)])

    @property
    def pages(self):
        yield self


DECIMAL_ARABIC = Name('D')
UPPERCASE_ROMAN = Name('R')
LOWERCASE_ROMAN = Name('r')
UPPERCASE_LETTERS = Name('A')
LOWERCASE_LETTERS = Name('a')


class PageLabel(Dictionary):
    type = 'PageLabel'

    def __init__(self, numbering_style=None, label_prefix=None, start=None):
        super().__init__(indirect=False)
        if numbering_style:
            self['S'] = numbering_style
        if label_prefix is not None:
            self['P'] = String(label_prefix)
        if start is not None:
            self['St'] = Integer(start)


class Outlines(Dictionary):
    type = 'Outlines'

    def __init__(self):
        super().__init__(indirect=True)


class OutlineEntry(Dictionary):
    def __init__(self, title, destination, parent):
        super().__init__(indirect=True)
        self['Title'] = String(title)
        self['Dest'] = String(destination)
        self['Parent'] = parent


class Rectangle(Array):
    def __init__(self, left, bottom, right, top, indirect=False):
        super().__init__([Real(value) for value in (left, bottom, right, top)],
                         indirect)


# interactivity

class Action(Dictionary):
    type = 'Action'
    action_type = None

    def __init__(self, next=None, indirect=False):
        super().__init__(indirect=indirect)
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
        super().__init__(indirect=indirect)
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

    def __init__(self, font, font_descriptor):
        super().__init__(indirect=True)
        self.font = font
        self.differences = {}
        self._free_codes = iter(i for i in chain(range(32, 255), range(0, 32))
                                if i not in self.font.encoding.values())
        self['BaseFont'] = Name(font.name)
        self['FontDescriptor'] = font_descriptor

    def get_code(self, glyph):
        try:
            try:
                return self.font.encoding[glyph.name]
            except KeyError:
                return self.differences[glyph.name]
        except KeyError:
            try:
                code = self.differences[glyph.name] = next(self._free_codes)
            except StopIteration:
                raise NotImplementedError('Encoding vector is full')
            return code

    def register_indirect(self, document, visited=None):
        if id(self) in visited:
            return
        try:
            self.font
        except AttributeError:    # this font was parsed from a PDF file
            pass
        else:
            for key in ('FirstChar', 'LastChar', 'Widths', 'Encoding'):
                if key in self:
                    self[key].delete(document)
                    del self[key]
            widths = {code: self.font._glyphs[name].width
                      for name, code in chain(self.font.encoding.items(),
                                              self.differences.items())}
            first, last = min(widths), max(widths)
            self['FirstChar'] = Integer(first)
            self['LastChar'] = Integer(last)
            self['Widths'] = Array((Integer(widths[c] if c in widths else 0)
                                    for c in range(first, last + 1)), True)
            if self.differences:
                self['Encoding'] = FontEncoding(differences=self.differences)
        return super().register_indirect(document, visited=visited)


class CompositeFont(Font):
    subtype = 'Type0'

    def __init__(self, descendant_font, encoding, to_unicode=None):
        super().__init__(indirect=True)
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
        super().__init__(indirect=False)
        self['Ordering'] = String(ordering)
        self['Registry'] = String(registry)
        self['Supplement'] = Integer(supplement)


class CIDFont(Font):
    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None):
        super().__init__(indirect=True)
        self['BaseFont'] = Name(base_font)
        self['FontDescriptor'] = font_descriptor
        self['CIDSystemInfo'] = cid_system_info
        self['DW'] = Integer(dw)
        if w:
            self['W'] = w

    def composite_font_name(self, encoding):
        raise NotImplementedError()


class CIDFontType0(CIDFont):
    # for embedding TrueType and OpenType/TTF fonts

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
    # for embedding OpenType/CFF fonts

    subtype = 'CIDFontType2'

    def __init__(self, base_font, cid_system_info, font_descriptor,
                 dw=1000, w=None, cid_to_gid_map=None):
        super().__init__(base_font, cid_system_info, font_descriptor, dw, w)
        if cid_to_gid_map:
            self['CIDToGIDMap'] = cid_to_gid_map

    def composite_font_name(self, encoding):
        return self['BaseFont']


FIXED_PITCH = 0x01
SERIF = 0x02
SYMBOLIC = 0x04
SCRIPT = 0x08
NONSYMBOLIC = 0x20
ITALIC = 0x40
ALL_CAP = 0x10000
SMALL_CAP = 0x20000
FORCE_BOLD = 0x40000


class FontDescriptor(Dictionary):
    type = 'FontDescriptor'

    def __init__(self, font, symbolic, font_file=None):
        super().__init__(indirect=True)
        self['FontName'] = Name(font.name)
        self['Flags'] = Integer(self.determine_flags(font, symbolic))
        self['FontBBox'] = Array([Integer(item) for item in font.bounding_box])
        self['ItalicAngle'] = Integer(font.italic_angle)
        self['Ascent'] = Integer(font.ascender)
        self['Descent'] = Integer(font.descender)
        self['CapHeight'] = Integer(font.cap_height)
        self['XHeight'] = Integer(font.x_height)
        self['StemV'] = Integer(font.stem_v)
        if font_file is not None:
            self[font_file.key] = font_file

    def determine_flags(self, font, symbolic):
        flags = SYMBOLIC if symbolic else NONSYMBOLIC
        if font.fixed_pitch:
            flags |= FIXED_PITCH
        if font.italic:
            flags |= ITALIC
        return flags


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


class TrueTypeFontFile(Stream):
    key = 'FontFile2'

    def __init__(self, font_data, filter=None):
        super().__init__(filter)
        self.write(font_data)


class OpenTypeFontFile(Stream):
    key = 'FontFile3'

    def __init__(self, font_data, filter=None):
        super().__init__(filter)
        self['Subtype'] = Name('OpenType')
        self.write(font_data)


class FontEncoding(Dictionary):
    def __init__(self, base_encoding=None, differences=None, indirect=True):
        super().__init__(indirect=indirect)
        self['Type'] = Name('Encoding')
        if base_encoding:
            self['BaseEncoding'] = Name(base_encoding)
        if differences:
            self['Differences'] = EncodingDifferences(differences)


class EncodingDifferences(Array):
    def __init__(self, differences):
        code_to_name = {code: name for name, code in differences.items()}
        last_code = float('+inf')
        array = []
        for code in sorted(code_to_name):
            if code != last_code + 1:
                array.append(Integer(code))
            array.append(Name(code_to_name[code]))
            last_code = code
        super().__init__(array)


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


from .xobject import XObjectForm
