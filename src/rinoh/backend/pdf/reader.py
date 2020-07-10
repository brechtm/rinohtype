# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct, time

from binascii import unhexlify
from io import SEEK_CUR, SEEK_END
from pathlib import Path

from ...util import all_subclasses
from . import cos
from .filter import Filter
from .xobject import XObjectForm


DICTIONARY_SUBCLASSES = {}
for cls in all_subclasses(cos.Dictionary):
    if cls.type is not None:
        DICTIONARY_SUBCLASSES.setdefault((cls.type, cls.subtype), cls)

FILTER_SUBCLASSES = {cls.name: cls for cls in all_subclasses(Filter)}



class PDFObjectReader(object):
    def __init__(self, file_or_filename, document=None):
        try:
            filename = Path(file_or_filename)
            self.file = filename.open('rb')
        except TypeError:
            self.file = file_or_filename
        self.document = document or self

    def jump_to_next_line(self):
        while True:
            char = self.file.read(1)
            if char == b'\n':
                break
            elif char == b'\r':
                next_char = self.file.read(1)
                if next_char != b'\n':
                    self.file.seek(-1, SEEK_CUR)
                break

    def eat_whitespace(self):
        while True:
            char = self.file.read(1)
            if char == b'':
                break
            if char not in cos.WHITESPACE:
                self.file.seek(-1, SEEK_CUR)
                break

    def next_token(self):
        token = self.file.read(1)
        if token in (cos.HexString.PREFIX, cos.HexString.POSTFIX):
            # check for dict begin/end
            char = self.file.read(1)
            if char == token:
                token += char
            else:
                self.file.seek(-1, SEEK_CUR)
        elif token in cos.DELIMITERS + cos.WHITESPACE:
            pass
        else:
            while True:
                char = self.file.read(1)
                if char in cos.DELIMITERS + cos.WHITESPACE:
                    self.file.seek(-1, SEEK_CUR)
                    break
                token += char
        return token

    def next_item(self, indirect=False):
        self.eat_whitespace()
        restore_pos = self.file.tell()
        token = self.next_token()
        if token == cos.String.PREFIX:
            item = self.read_string(indirect)
        elif token == cos.HexString.PREFIX:
            item = self.read_hex_string(indirect)
        elif token == cos.Array.PREFIX:
            item = self.read_array(indirect)
        elif token == cos.Name.PREFIX:
            item = self.read_name(indirect)
        elif token == cos.Dictionary.PREFIX:
            item = self.read_dictionary_or_stream(indirect)
        elif token == b'true':
            item = cos.Boolean(True, indirect=indirect)
        elif token == b'false':
            item = cos.Boolean(False, indirect=indirect)
        elif token == b'null':
            item = cos.Null(indirect=indirect)
        else:
            # number or indirect reference
            self.file.seek(restore_pos)
            item = self.read_number(indirect)
            restore_pos = self.file.tell()
            if isinstance(item, cos.Integer):
                try:
                    generation = self.read_number()
                    self.eat_whitespace()
                    r = self.next_token()
                    if isinstance(generation, cos.Integer) and r == b'R':
                        item = cos.Reference(self.document, int(item),
                                             int(generation))
                    else:
                        raise ValueError
                except ValueError:
                    self.file.seek(restore_pos)
        return item

    def peek(self, length=50):
        restore_pos = self.file.tell()
        print(self.file.read(length))
        self.file.seek(restore_pos)

    # TODO: move reader function outside to simplify unit testing
    def read_array(self, indirect=False):
        array = cos.Array(indirect=indirect)
        while True:
            self.eat_whitespace()
            token = self.file.read(1)
            if token == cos.Array.POSTFIX:
                break
            self.file.seek(-1, SEEK_CUR)
            item = self.next_item()
            array.append(item)
        return array

    def read_name(self, indirect=False):
        name = b''
        while True:
            char = self.file.read(1)
            if char in cos.DELIMITERS + cos.WHITESPACE:
                self.file.seek(-1, SEEK_CUR)
                break
            elif char == b'#':
                char_code = self.file.read(2)
                char = chr(int(char_code.decode('ascii'), 16)).encode('ascii')
            name += char
        return cos.Name(name, indirect=indirect)

    def read_dictionary_or_stream(self, indirect=False):
        dictionary = cos.Dictionary(indirect=indirect)
        while True:
            self.eat_whitespace()
            token = self.next_token()
            if token == cos.Dictionary.POSTFIX:
                break
            key, value = self.read_name(), self.next_item()
            dictionary[key] = value
        self.eat_whitespace()
        dict_pos = self.file.tell()
        if self.next_token() == b'stream':
            self.jump_to_next_line()
            length = int(dictionary['Length'])
            if 'Filter' in dictionary:
                filter_or_filters = dictionary['Filter']
                if isinstance(filter_or_filters, cos.Name):
                    filter_class = FILTER_SUBCLASSES[filter_or_filters]
                    try:
                        decode_params = dictionary['DecodeParms']
                        decode_params.__class__ = filter_class.params_class
                    except KeyError:
                        decode_params = None
                    stream_filter = filter_class(params=decode_params)
                else:
                    filter_classes = [FILTER_SUBCLASSES[filter_name]
                                      for filter_name in filter_or_filters]
                    try:
                        stream_filter = []
                        for fltr_cls, params in zip(filter_classes,
                                                    dictionary['DecodeParms']):
                            if params:
                                params.__class__ = fltr_cls.params_class
                            stream_filter.append(fltr_cls(params=params))
                    except KeyError:
                        stream_filter = [filter_class()
                                         for filter_class in filter_classes]
            else:
                stream_filter = None
            stream = cos.Stream(stream_filter)
            stream.update(dictionary)
            stream._data.write(self.file.read(length))
            self.eat_whitespace()
            assert self.next_token() == b'endstream'
            dictionary = stream
        else:
            self.file.seek(dict_pos)
        # try to map to specific Dictionary sub-class
        type = dictionary.get('Type', None)
        subtype = dictionary.get('Subtype', None)
        key = str(type) if type else None, str(subtype) if subtype else None
        if key in DICTIONARY_SUBCLASSES:
            dictionary.__class__ = DICTIONARY_SUBCLASSES[key]
        return dictionary

    escape_chars = b'nrtbf()\\'

    def read_string(self, indirect=False):
        string = b''
        escape = False
        parenthesis_level = 0   # TODO: is currently not used
        while True:
            char = self.file.read(1)
            if escape:
                if char in self.escape_chars:
                    string += char
                elif char == b'\n':
                    pass
                elif char == b'\r' and self.file.read(1) != '\n':
                    self.file.seek(-1, SEEK_CUR)
                elif char.isdigit():
                    for i in range(2):
                        extra = self.file.read(1)
                        if extra.isdigit():
                            char += extra
                        else:
                            self.file.seek(-1, SEEK_CUR)
                            break
                    string += struct.pack('B', int(char, 8))
                else:
                    string += b'\\' + char
                escape = False
            elif char == b'\\':
                escape = True
            elif char == b'(':
                parenthesis_level += 1
            elif char == b')' and parenthesis_level > 0:
                parenthesis_level -= 1
            elif char == cos.String.POSTFIX:
                break
            else:
                string += char
        return cos.String(string, indirect=indirect)

    def read_hex_string(self, indirect=False):
        hex_string = b''
        while True:
            self.eat_whitespace()
            char = self.file.read(1)
            if char == cos.HexString.POSTFIX:
                break
            hex_string += char
        if len(hex_string) % 2 > 0:
            hex_string += b'0'
        return cos.HexString(unhexlify(hex_string), indirect=indirect)

    def read_number(self, indirect=False):
        self.eat_whitespace()
        number_string = b''
        while True:
            char = self.file.read(1)
            if not char:
                break
            elif char not in b'+-.0123456789':
                self.file.seek(-1, SEEK_CUR)
                break
            number_string += char
        try:
            number = cos.Integer(number_string, indirect=indirect)
        except ValueError:
            number = cos.Real(number_string, indirect=indirect)
        return number


class PDFReader(PDFObjectReader, cos.Document):
    PDF_SIGNATURE = b'%PDF'

    def __init__(self, file_or_filename):
        super().__init__(file_or_filename)
        self.file.seek(0)
        if self.file.read(len(self.PDF_SIGNATURE)) != self.PDF_SIGNATURE:
            raise ValueError('Not a PDF file: missing %PDF signature')
        self.timestamp = time.time()
        self._by_object_id = {}
        xref_offset = self.find_xref_offset()
        try:
            self._xref, trailer = self.parse_xref_stream(xref_offset)
        except ValueError:
            self._xref, trailer = self.parse_xref_table(xref_offset)
        if 'Info' in trailer:
            self.info = trailer['Info']
        else:
            self.info = cos.Dictionary()
        self.id = trailer['ID'] if 'ID' in trailer else None
        self._max_identifier_in_file = int(trailer['Size']) - 1
        self.catalog = trailer['Root']
        self.dests = cos.Dictionary()
        try:
            dests_names = iter(self.catalog['Names']['Dests']['Names'])
            for name in dests_names:
                dest = next(dests_names)
                self.dests[name] = dest
        except KeyError:
            pass

    @property
    def max_identifier(self):
        return max(super().max_identifier, self._max_identifier_in_file)

    def __getitem__(self, identifier):
        try:
            obj = super().__getitem__(identifier)
        except KeyError:
            obj = self[identifier] = self._xref.get_object(identifier)
        return obj

    def __delitem__(self, identifier):
        del self._xref[identifier]
        super().__delitem__(identifier)

    def parse_trailer(self):
        assert self.next_token() == b'trailer'
        self.jump_to_next_line()
        trailer_dict = self.next_item()
        return trailer_dict
##/Size: (Required; must not be an indirect reference) The total number of entries in the file's
##cross-reference table, as defined by the combination of the original section and all
##update sections. Equivalently, this value is 1 greater than the highest object number
##used in the file.
##Note: Any object in a cross-reference section whose number is greater than this value is
##ignored and considered missing.

    def parse_indirect_object(self, address):
        # save file state
        restore_pos = self.file.tell()
        self.file.seek(address)
        identifier = int(self.read_number())
        generation = int(self.read_number())
        self.eat_whitespace()
        assert self.next_token() == b'obj'
        self.eat_whitespace()
        obj = self.next_item(indirect=True)
        reference = cos.Reference(self, identifier, generation)
        self._by_object_id[id(obj)] = reference
        self.eat_whitespace()
        assert self.next_token() == b'endobj'
        self.file.seek(restore_pos)
        return identifier, obj

    def parse_xref_table(self, offset):
        xref = XRefTable(self)
        self.file.seek(offset)
        assert self.next_token() == b'xref'
        while True:
            try:
                first, total = int(self.read_number()), self.read_number()
                self.jump_to_next_line()
                for identifier in range(first, first + total):
                    line = self.file.read(20)
                    fields = identifier, int(line[:10]), int(line[11:16])
                    if line[17] == ord(b'n'):
                        xref[identifier] = IndirectObjectEntry(*fields)
                    else:
                        assert line[17] == ord(b'f')
                        xref[identifier] = FreeObjectEntry(*fields)
            except ValueError:
                break
        trailer = self.parse_trailer()
        prev_xref = xref_stm = None
        if 'Prev' in trailer:
            prev_xref, prev_trailer = self.parse_xref_table(trailer['Prev'])
        if 'XRefStm' in trailer:
            xref_stm, _ = self.parse_xref_stream(trailer['XRefStm'])
            xref_stm.prev = prev_xref
        xref.prev = xref_stm or prev_xref
        return xref, trailer

    def parse_xref_stream(self, offset):
        identifier, xref_stream = self.parse_indirect_object(offset)
        self[identifier] = xref_stream
        if 'Prev' in xref_stream:
            prev = self.parse_indirect_object(xref_stream['Prev'])
        else:
            prev = None
        xref = XRefTable(self, prev)
        size = int(xref_stream['Size'])
        widths = [int(width) for width in xref_stream['W']]
        assert len(widths) == 3
        assert max(widths) <= 8
        if 'Index' in xref_stream:
            index = iter(int(value) for value in xref_stream['Index'])
        else:
            index = (0, size)
        xref_stream.seek(0)
        while True:
            try:
                first, total = next(index), next(index)
            except StopIteration:
                break
            for identifier in range(first, first + total):
                values = (xref_stream.read(width) for width in widths)
                fields = [struct.unpack('>Q', value.rjust(8, b'\x00'))[0]
                          for value in values]
                if widths[0] == 0:
                    field_type = 1
                else:
                    field_type = fields[0]
                    fields = fields[1:]
                field_class = FIELD_CLASSES[field_type]
                xref[identifier] = field_class(identifier, *fields)
        assert identifier + 1 == size
        return xref, xref_stream

    EOF_MARKER = b'%%EOF'
    START_XREF = b'startxref'

    def find_xref_offset(self):
        offset = self.file.seek(- len(self.EOF_MARKER), SEEK_END)
        for i in range(10):
            self.file.seek(offset)
            if self.file.read(len(self.EOF_MARKER)) == self.EOF_MARKER:
                break
            offset -= 1
        else:
            raise ValueError('Not a PDF file: missing %%EOF')
        offset -= len(self.START_XREF)
        while True:
            self.file.seek(offset)
            value = self.file.read(len(self.START_XREF))
            if value == self.START_XREF:
                self.jump_to_next_line()
                xref_offset = self.read_number()
                break
            offset -= 1
        return int(xref_offset)

    def iter_outlines(self, depth=float('+inf')):
        """Iterate over the outline entries up to a given depth

        Args:
            depth (int): the maximum depth of outline entries to yield

        Returns:
            Iterator[(int, String, Array)]: entry depth, title and destination

        """
        try:
            outlines = self.catalog['Outlines']
            entry = outlines['First']
        except KeyError:
            return
        stack = [outlines]
        while True:
            entry_depth = len(stack) - 1
            dest = entry['Dest']
            yield (entry_depth, entry['Title'],
                   dest if isinstance(dest, cos.Array) else self.dests[dest])
            if 'First' in entry and depth > entry_depth:
                stack.append(entry)
                entry = entry['First']
            elif 'Next' in entry:
                entry = entry['Next']
            else:
                while stack:
                    parent = stack.pop()
                    if 'Next' in parent:
                        entry = parent['Next']
                        break
                else:
                    break


class XRefTable(dict):
    def __init__(self, document, prev=None):
        self.document = document
        self.prev = prev

    def get_object(self, identifier):
        try:
            return self[identifier].get_object(self.document)
        except KeyError:
            return self.prev.get_object(identifier)


class XRefEntry(object):
    def get_object(self, document):
        raise NotImplementedError


class FreeObjectEntry(XRefEntry):
    def __init__(self, identifier, next_free_object_identifier, generation):
        self.identifier = identifier
        self.next_free_object_identifier = next_free_object_identifier
        self.generation = generation

    def get_object(self, document):
        raise Exception('Cannot retieve a free object with id {}'
                        .format(self.identifier))


class IndirectObjectEntry(XRefEntry):
    def __init__(self, identifier, address, generation=0):
        self.identifier = identifier
        self.address = address
        self.generation = generation

    def get_object(self, document):
        obj_identifier, obj = document.parse_indirect_object(self.address)
        assert obj_identifier == self.identifier
        return obj


class CompressedObjectEntry(XRefEntry):
    def __init__(self, identifier, object_stream_identifier, object_index):
        self.identifier = identifier
        self.object_stream_identifier = object_stream_identifier
        self.object_index = object_index

    def get_object(self, document):
        object_stream = document[self.object_stream_identifier]
        return object_stream.get_object(document, self.object_index)


FIELD_CLASSES = {0: FreeObjectEntry,
                 1: IndirectObjectEntry,
                 2: CompressedObjectEntry}


class PDFPageReader(XObjectForm):
    def __init__(self, file_or_filename, page_number=1):
        pdf_file = PDFReader(file_or_filename)
        page = pdf_file.get_page(page_number - 1)
        super().__init__(page['MediaBox'])
        content_stream = page['Contents']
        if 'Filter' in content_stream:
            self['Filter'] = content_stream['Filter']
        if 'Resources' in page:
            self['Resources'] = page['Resources']
        self.write(content_stream.getvalue())

    @property
    def width(self):
        _, _, width, _ = self['BBox']
        return width

    @property
    def height(self):
        _, _, _, height = self['BBox']
        return height

    @property
    def dpi(self):
        return None, None
