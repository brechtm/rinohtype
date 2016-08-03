# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct

from binascii import hexlify
from io import BytesIO


def grab(file, data_format):
    data = file.read(struct.calcsize(data_format))
    return struct.unpack('>' + data_format, data)


card8 = lambda file: grab(file, 'B')[0]
card16 = lambda file: grab(file, 'h')[0]
offsize = card8

def offset(offset_size):
    return lambda file: grab(file, ('B', 'H', 'I', 'L')[offset_size - 1])[0]


class Section(dict):
    def __init__(self, file, offset=None):
        if offset:
            file.seek(offset)
        for name, reader in self.entries:
            self[name] = reader(file)


class Header(Section):
    entries = [('major', card8),
               ('minor', card8),
               ('hdrSize', card8),
               ('offSize', card8)]


class OperatorExeption(Exception):
    def __init__(self, code):
        self.code = code


class Operator(object):
    def __init__(self, name, type, default=None):
        self.name = name
        self.type = type
        self.default = default

    def __repr__(self):
        return "<Operator {}>".format(self.name)


number = lambda array: array[0]
sid = number
boolean = lambda array: number(array) == 1
array = lambda array: array

def delta(array):
    delta = []
    last_value = 0
    for item in array:
        delta.append(last_value + item)
        last_value = item


class Dict(dict):
    # values (operands) - key (operator) pairs
    def __init__(self, file, length, offset=None):
        if offset is not None:
            file.seek(offset)
        else:
            offset = file.tell()
        operands = []
        while file.tell() < offset + length:
            try:
                operands.append(self._next_token(file))
            except OperatorExeption as e:
                operator = self.operators[e.code]
                self[operator.name] = operator.type(operands)
                operands = []

    def _next_token(self, file):
        b0 = card8(file)
        if b0 == 12:
            raise OperatorExeption((12, card8(file)))
        elif b0 <= 22:
            raise OperatorExeption(b0)
        elif b0 == 28:
            return grab(file, 'h')[0]
        elif b0 == 29:
            return grab(file, 'i')[0]
        elif b0 == 30: # real
            real_string = ''
            while True:
                real_string += hexlify(file.read(1)).decode('ascii')
                if 'f' in real_string:
                    real_string = (real_string.replace('a', '.')
                                              .replace('b', 'E')
                                              .replace('c', 'E-')
                                              .replace('e', '-')
                                              .rstrip('f'))
                    return float(real_string)
        elif b0 < 32:
            raise NotImplementedError()
        elif b0 < 247:
            return b0 - 139
        elif b0 < 251:
            b1 = card8(file)
            return (b0 - 247) * 256 + b1 + 108
        elif b0 < 255:
            b1 = card8(file)
            return - (b0 - 251) * 256 - b1 - 108
        else:
            raise NotImplementedError()


class TopDict(Dict):
    operators = {0: Operator('version', sid),
                 1: Operator('Notice', sid),
                 (12, 0): Operator('Copyright', sid),
                 2: Operator('FullName', sid),
                 3: Operator('FamilyName', sid),
                 4: Operator('Weight', sid),
                 (12, 1): Operator('isFixedPitch', boolean, False),
                 (12, 2): Operator('ItalicAngle', number, 0),
                 (12, 3): Operator('UnderlinePosition', number, -100),
                 (12, 4): Operator('UnderlineThickness', number, 50),
                 (12, 5): Operator('PaintType', number, 0),
                 (12, 6): Operator('CharstringType', number, 2),
                 (12, 7): Operator('FontMatrix', array, [0.001, 0, 0, 0.001, 0, 0]),
                 13: Operator('UniqueID', number),
                 5: Operator('FontBBox', array, [0, 0, 0, 0]),
                 (12, 8): Operator('StrokeWidth', number, 0),
                 14: Operator('XUID', array),
                 15: Operator('charset', number, 0), # charset offset (0)
                 16: Operator('Encoding', number, 0), # encoding offset (0)
                 17: Operator('CharStrings', number), # CharStrings offset (0)
                 18: Operator('Private', array), # Private DICT size
                                                           # and offset (0)
                 (12, 20): Operator('SyntheticBase', number), # synthetic base font index
                 (12, 21): Operator('PostScript', sid), # embedded PostScript language code
                 (12, 22): Operator('BaseFontName', sid), # (added as needed by Adobe-based technology)
                 (12, 23): Operator('BaseFontBlend', delta)} # (added as needed by Adobe-based technology)


class Index(list):
    """Array of variable-sized objects"""
    def __init__(self, file, offset_=None):
        if offset_ is not None:
            file.seek(offset_)
        count = card16(file)
        offset_size = card8(file)
        self.offsets = []
        self.sizes = []
        for i in range(count + 1):
            self.offsets.append(offset(offset_size)(file))
        self.offset_reference = file.tell() - 1
        for i in range(count):
            self.sizes.append(self.offsets[i + 1] - self.offsets[i])


class NameIndex(Index):
    def __init__(self, file, offset=None):
        super().__init__(file, offset)
        for name_offset, size in zip(self.offsets, self.sizes):
            file.seek(self.offset_reference + name_offset)
            name = file.read(size).decode('ascii')
            self.append(name)


class TopDictIndex(Index):
    def __init__(self, file, offset=None):
        super().__init__(file, offset)
        for dict_offset, size in zip(self.offsets, self.sizes):
            self.append(TopDict(file, size, self.offset_reference + dict_offset))


class CompactFontFormat(object):
    def __init__(self, file, offset):
        if offset is not None:
            file.seek(offset)
        self.header = Header(file)
        assert self.header['major'] == 1
        self.name = NameIndex(file, offset + self.header['hdrSize'])
        self.top_dicts = TopDictIndex(file)
        #String INDEX
        #Global Subr INDEX
        # -------------------
        #Encodings
        #Charsets
        #FDSelect (CIDFonts only)
        #CharStrings INDEX (per-font) <=========================================
        #Font DICT INDEX (per-font, CIDFonts only)
        #Private DICT (per-font)
        #Local Subr INDEX (per-font or per-Private DICT for CIDFonts)
        #Copyright and Trademark Notices
