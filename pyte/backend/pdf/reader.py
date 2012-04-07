
import re, struct, time

from binascii import unhexlify
from collections import OrderedDict
from io import BytesIO, SEEK_CUR, SEEK_END

from . import cos


class PDFReader(cos.Document):
    DICT_BEGIN = b'<<'
    DICT_END = b'>>'
    STRING_BEGIN = b'('
    STRING_END = b')'
    ARRAY_BEGIN = b'['
    ARRAY_END = b']'
    HEXSTRING_BEGIN = b'<'
    HEXSTRING_END = b'>'
    NAME_BEGIN = b'/'
    COMMENT_BEGIN = b'%'

    def __init__(self, file_or_filename):
        try:
            self.file = open(file_or_filename, 'rb')
        except TypeError:
            self.file = file_or_filename
        self.timestamp = time.time()
        xref_offset = self.find_xref_offset()
        self._xref = self.parse_xref_tables(xref_offset)
        trailer = self.parse_trailer()
        if 'Info' in trailer:
            self.info = trailer['Info'].target
        else:
            self.info = Dictionary(self)
        self.id = trailer['ID'] if 'ID' in trailer else None
        self._max_identifier_in_file = int(trailer['Size']) - 1
        self.catalog = trailer['Root'].target

    @property
    def max_identifier(self):
        return max(super().max_identifier, self._max_identifier_in_file)

    def __getitem__(self, identifier):
        try:
            obj_gen = super().__getitem__(identifier)
        except KeyError:
            address = self._xref[identifier]
            obj_gen = self.parse_indirect_object(address)
            self[identifier] = obj_gen
        return obj_gen

    def __delitem__(self, identifier):
        del self._xref[identifier]
        super().__delitem__(identifier)

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

    whitespace = b'\0\t\n\f\r '
    delimiters = b'()<>[]{}/%'

    def eat_whitespace(self):
        while True:
            char = self.file.read(1)
            if char not in self.whitespace:
                self.file.seek(-1, SEEK_CUR)
                break

    def next_token(self):
        token = self.file.read(1)
        if token in (self.HEXSTRING_BEGIN, self.HEXSTRING_END):
            # check for dict begin/end
            char = self.file.read(1)
            if char == token:
                token += char
            else:
                self.file.seek(-1, SEEK_CUR)
        elif token in self.delimiters + self.whitespace:
            pass
        else:
            while True:
                char = self.file.read(1)
                if char in self.delimiters + self.whitespace:
                    self.file.seek(-1, SEEK_CUR)
                    break
                token += char
        return token

    def next_item(self):
        self.eat_whitespace()
        restore_pos = self.file.tell()
        token = self.next_token()
        if token == self.STRING_BEGIN:
            item = self.read_string()
        elif token == self.HEXSTRING_BEGIN:
            item = self.read_hex_string()
        elif token == self.ARRAY_BEGIN:
            item = self.read_array()
        elif token == self.NAME_BEGIN:
            item = self.read_name()
        elif token == self.DICT_BEGIN:
            item = self.read_dictionary()
            self.eat_whitespace()
            dict_pos = self.file.tell()
            if self.next_token() == b'stream':
                self.eat_whitespace()
                length = int(item['Length'])
                stream = cos.Stream(None)
                stream.update(item)
                stream.write(self.file.read(length))
                item = stream
            else:
                self.file.seek(dict_pos)
        elif token == b'true':
            item = cos.Boolean(True)
        elif token == b'false':
            item = cos.Boolean(False)
        elif token == b'null':
            item = cos.Null()
        else:
            # number or indirect reference
            self.file.seek(restore_pos)
            item = self.read_number()
            restore_pos = self.file.tell()
            if isinstance(item, cos.Integer):
                try:
                    generation = self.read_number()
                    self.eat_whitespace()
                    r = self.next_token()
                    if isinstance(generation, cos.Integer) and r == b'R':
                        item = cos.Reference(self, int(item), int(generation))
                    else:
                        raise ValueError
                except ValueError:
                    self.file.seek(restore_pos)
        return item

    def peek(self):
        restore_pos = self.file.tell()
        print(self.file.read(20))
        self.file.seek(restore_pos)

    def read_array(self):
        array = cos.Array()
        while True:
            self.eat_whitespace()
            token = self.file.read(1)
            if token == self.ARRAY_END:
                break
            self.file.seek(-1, SEEK_CUR)
            item = self.next_item()
            array.append(item)
        return array

    re_name_escape = re.compile(r'#\d\d')

    def read_name(self):
        name = ''
        while True:
            char = self.file.read(1)
            if char in self.delimiters + self.whitespace:
                self.file.seek(-1, SEEK_CUR)
                break
            name += char.decode('utf_8')
        for group in set(self.re_name_escape.findall(name)):
            number = int(group[1:], 16)
            name.replace(group, chr(number))
        return cos.Name(name)

    def read_dictionary(self):
        dictionary = cos.Dictionary()
        while True:
            self.eat_whitespace()
            token = self.next_token()
            if token == self.DICT_END:
                break
            key, value = self.read_name(), self.next_item()
            dictionary[key.name] = value
        return dictionary

    newline_chars = b'\n\r'
    escape_chars = b'nrtbf()\\'

    def read_string(self):
        string = b''
        escape = False
        parenthesis_level = 0
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
            elif char == self.STRING_END:
                break
            else:
                string += char
        return cos.String(string.decode('utf_8'))

    def read_hex_string(self):
        hex_string = b''
        while True:
            self.eat_whitespace()
            char = self.file.read(1)
            if char == self.HEXSTRING_END:
                break
            hex_string += char
        if len(hex_string) % 2 > 0:
            hex_string += b'0'
        return cos.HexString(unhexlify(hex_string))

    def read_number(self):
        self.eat_whitespace()
        number = b''
        while True:
            char = self.file.read(1)
            if char not in b'+-.0123456789':
                self.file.seek(-1, SEEK_CUR)
                break
            number += char
        try:
            number = cos.Integer(number)
        except ValueError:
            number = cos.Real(number)
        return number

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
        self.eat_whitespace()
        generation = int(self.read_number())
        self.eat_whitespace()
        self.next_token()   # 'obj'
        self.eat_whitespace()
        obj = self.next_item()
        obj.document = self
        obj.reference = cos.Reference(self, identifier, generation)
        self.file.seek(restore_pos)
        return obj, generation

    def parse_xref_tables(self, offset):
        xref = {}
        self.file.seek(offset)
        assert self.next_token() == b'xref'
        self.jump_to_next_line()
        while True:
            try:
                identifier, entries = self.read_number(), self.read_number()
                self.jump_to_next_line()
                for i in range(entries):
                    line = self.file.read(20)
                    if line[17] == ord(b'n'):
                        address, generation = int(line[:10]), int(line[11:16])
                        xref[identifier] = address
                    identifier += 1
            except ValueError:
                break
        return xref

    def find_xref_offset(self):
        self.file.seek(0, SEEK_END)
        offset = self.file.tell() - len('%%EOF')
        while True:
            self.file.seek(offset)
            value = self.file.read(len('startxref'))
            if value == b'startxref':
                self.jump_to_next_line()
                xref_offset = self.read_number()
                self.jump_to_next_line()
                if self.file.read(5) != b'%%EOF':
                    raise ValueError('Invalid PDF file: missing %%EOF')
                break
            offset -= 1
        return int(xref_offset)
