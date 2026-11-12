# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import math, io, struct

from datetime import datetime, timedelta
from collections import OrderedDict

from ...util import all_subclasses


class ValueReader(object):
    """Reader for a single value"""

    def __init__(self, data_format, process_struct=None):
        self.data_format = data_format
        self.struct = struct.Struct('>' + data_format)
        self.unpack = self.struct.unpack
        self.process_struct = process_struct

    def __call__(self, file, **kwargs):
        data = self.unpack(file.read(self.struct.size))
        if self.process_struct:
            return self.process_struct(data)
        return data[0]

    def __len__(self):
        return self.struct.size

    def __getitem__(self, length):
        """Reader for an array of values

        An integer `length` is the number of values to read; a string is the
        key of the table entry holding the number of values (a context
        array).

        """
        if isinstance(length, int):
            return ArrayReader(self, length)
        elif isinstance(length, str):
            return ContextArrayReader(self, length)
        raise TypeError('invalid length: {!r}'.format(length))


class ArrayReader(object):
    """Reader for an array of values or objects"""

    def __init__(self, reader, length):
        self.reader = reader
        self.length = length
        if hasattr(reader, 'data_format'):      # a value reader
            self.struct = struct.Struct('>' + reader.data_format * length)
            self.unpack = self.struct.unpack
        else:               # a table or record; parse the items one by one
            self.struct = None

    def __call__(self, file, *args, **kwargs):
        if self.struct is None:
            return [self.reader(file, *args, **kwargs)
                    for _ in range(self.length)]
        data = self.unpack(file.read(self.struct.size))
        if self.reader.process_struct:
            size = len(data) // self.length if data else 0
            items = zip(*[iter(data)] * size)
            return [self.reader.process_struct(item) for item in items]
        return list(data)


class ContextArrayReader(object):
    """Reader for an array of which the length is stored in the table

    The length is looked up in the table under `length_key` and multiplied by
    `multiplier` (e.g. 0.5 for a count that is specified in bytes). Optional
    `indirect_args` specify further table entries passed on to the item
    reader.

    """

    def __init__(self, reader, length_key, *indirect_args, multiplier=1):
        self.reader = reader
        self.length_key = length_key
        self.indirect_args = indirect_args
        self.multiplier = multiplier

    def __call__(self, file, table, **kwargs):
        length = int(table[self.length_key] * self.multiplier)
        args = [table[key] for key in self.indirect_args]
        return ArrayReader(self.reader, length)(file, *args, table=table,
                                                **kwargs)


create_reader = ValueReader
array = ArrayReader
context_array = ContextArrayReader


# using the names and datatypes from the OpenType specification
# http://www.microsoft.com/typography/otspec/
byte = create_reader('B')
char = create_reader('b')
ushort = create_reader('H')
short = create_reader('h')
ulong = create_reader('L')
long = create_reader('l')
fixed = create_reader('L', lambda data: data[0] / 2**16)
int16 = fword = short
uint16 = ufword = ushort
uint24 = create_reader('3B', lambda data: (data[0] << 16) | (data[1] << 8)
                                           | data[2])
string = create_reader('4s', lambda data: data[0].decode('ascii').strip())
tag = string
glyph_id = uint16
offset = uint16

longdatetime = create_reader('q', lambda data: datetime(1904, 1, 1)
                                               + timedelta(seconds=data[0]))


class Packed(OrderedDict):
    reader = None
    fields = []

    def __init__(self, file, **kwargs):
        super().__init__(self)
        self.value = self.__class__.reader(file)
        for name, mask, processor in self.fields:
            self[name] = processor(self.value & mask)


def context(reader, *indirect_args):
    def context_reader(file, base, table):
        args = [table[key] for key in indirect_args]
        return reader(file, *args)
    return context_reader


def indirect(reader, *indirect_args, offset_reader=offset):
    def indirect_reader(file, base, table, **kwargs):
        indirect_offset = offset_reader(file)
        if indirect_offset == 0:    # no table present
            return None
        restore_position = file.tell()
        args = [table[key] for key in indirect_args]
        result = reader(file, base + indirect_offset, *args, **kwargs)
        file.seek(restore_position)
        return result
    return indirect_reader


def indirect_array(reader, count_key, *indirect_args):
    def indirect_array_reader(file, base, table):
        offsets = offset[table[count_key]](file)
        args = [table[key] for key in indirect_args]
        return [reader(file, base + entry_offset, *args)
                for entry_offset in offsets]
    return indirect_array_reader


class OpenTypeTableBase(OrderedDict):
    entries = []

    def __init__(self, file, file_offset=None, **kwargs):
        super().__init__()
        if file_offset is None:
            file_offset = kwargs.pop('base', None)
        self.parse(file, file_offset, self.entries, **kwargs)

    def parse(self, file, base, entries, **kwargs):
        kwargs.pop('table', None)
        for key, reader in entries:
            value = reader(file, base=base, table=self, **kwargs)
            if key is not None:
                self[key] = value


class OpenTypeTable(OpenTypeTableBase):
    tag = None

    def __init__(self, file, file_offset=None, **kwargs):
        if file_offset is not None:
            file.seek(file_offset)
        super().__init__(file, file_offset, **kwargs)



class MultiFormatTable(OpenTypeTable):
    formats = {}

    def __init__(self, file, file_offset=None, **kwargs):
        super().__init__(file, file_offset, **kwargs)
        table_format = self[self.entries[0][0]]
        if table_format in self.formats:
            self.parse(file, file_offset, self.formats[table_format])


class Record(OpenTypeTableBase):
    """The base offset for indirect entries in a `Record` is the parent table's
    base, not the `Record`'s base."""
    def __init__(self, file, table=None, base=None):
        super().__init__(file, base)
        self._parent_table = table


class OffsetTable(OpenTypeTable):
    entries = [('sfnt version', fixed),
               ('numTables', ushort),
               ('searchRange', ushort),
               ('entrySelector', ushort),
               ('rangeShift', ushort)]


class TableRecord(OpenTypeTable):
    entries = [('tag', tag),
               ('checkSum', ulong),
               ('offset', ulong),
               ('length', ulong)]

    def check_sum(self, file):
        file.seek(self['offset'])
        num_values = math.ceil(self['length'] / 4)    # padded to 4 bytes
        data = file.read(4 * num_values).ljust(4 * num_values, b'\0')
        values = struct.unpack('>{}L'.format(num_values), data)
        total = sum(values)
        if self['tag'] == 'head':
            total -= values[2]      # skip checkSumAdjustment
        checksum = total % 2**32
        assert checksum == self['checkSum']


from .required import HmtxTable
from .cff import CompactFontFormat
from . import gpos, gsub, other


class OpenTypeParser(dict):
    """The tables in an OpenType font file, parsed on first access"""

    def __init__(self, filename):
        with open(filename, 'rb') as disk_file:
            self._file = file = io.BytesIO(disk_file.read())
        offset_table = OffsetTable(file)
        self._table_records = {}
        for i in range(offset_table['numTables']):
            record = TableRecord(file)
            self._table_records[record['tag']] = record

    def __contains__(self, tag):
        return tag in self._table_records

    def __missing__(self, tag):
        file, record = self._file, self._table_records[tag]
        record.check_sum(file)
        if tag == 'hmtx':
            table = HmtxTable(file, record['offset'],
                              self['hhea']['numberOfHMetrics'],
                              self['maxp']['numGlyphs'])
        elif tag == 'CFF':
            table = CompactFontFormat(file, record['offset'])
        else:
            table = self._parse_table(file, record)
        self[tag] = table
        return table

    @staticmethod
    def _parse_table(file, table_record):
        for cls in all_subclasses(OpenTypeTable):
            if cls.tag == table_record['tag']:
                return cls(file, table_record['offset'])
