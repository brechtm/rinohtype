
import hashlib, math, io, struct
from datetime import datetime, timedelta
from collections import OrderedDict

from ...util import recursive_subclasses


def create_reader(data_format, process_struct=lambda data: data[0]):
    data_struct = struct.Struct('>' + data_format)
    def reader(file):
        data = data_struct.unpack(file.read(data_struct.size))
        return process_struct(data)
    return reader


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
uint24 = create_reader('3B', lambda data: sum([byte << (2 - i)
                                           for i, byte in enumerate(data)]))
string = create_reader('4s', lambda data: data[0].decode('ascii').strip())
tag = string
glyph_id = uint16
offset = uint16

def longdatetime(file):
    return longdatetime._epoch + timedelta(seconds=longdatetime._grabber(file))

longdatetime._epoch = datetime(1904, 1, 1, 12)
longdatetime._grabber = create_reader('Q')


class Packed(OrderedDict):
    reader = None
    fields = []

    def __init__(self, file):
        super().__init__(self)
        self.value = self.__class__.reader(file)
        for name, mask, processor in self.fields:
            self[name] = processor(self.value & mask)


def array(reader, length):
    def array_reader(file, **kwargs):
        return [reader(file, **kwargs) for i in range(length)]
    return array_reader


def context_array(reader, count_key, multiplier=1):
    def context_array_reader(file, table=None, **kwargs):
        length = int(table[count_key] * multiplier)
        try:
            return array(reader, length)(file, table=table, **kwargs)
        except TypeError as e:
            return array(reader, length)(file)
    return context_array_reader


def indirect(reader, *args, offset_reader=offset):
    def indirect_reader(file, base, **kwargs):
        indirect_offset = offset_reader(file)
        restore_position = file.tell()
        result = reader(file, base + indirect_offset, *args)
        file.seek(restore_position)
        return result
    return indirect_reader


def indirect_array(reader, count_key, *indirect_args):
    def indirect_array_reader(file, base, table):
        offsets = array(offset, table[count_key])(file)
        args = [table[key] for key in indirect_args]
        return [reader(file, base + entry_offset, *args)
                for entry_offset in offsets]
    return indirect_array_reader


class OpenTypeTableBase(OrderedDict):
    entries = []

    def __init__(self, file, file_offset=None):
        super().__init__()
        self.parse(file, file_offset, self.entries)

    def parse(self, file, base, entries):
        for key, reader in entries:
            try: # special readers
                value = reader(file, base=base, table=self)
            except TypeError: # table reader or simple reader
                value = reader(file)
            if key is not None:
                self[key] = value


class OpenTypeTable(OpenTypeTableBase):
    tag = None

    def __init__(self, file, file_offset=None):
        if file_offset is not None:
            file.seek(file_offset)
        super().__init__(file, file_offset)



class MultiFormatTable(OpenTypeTable):
    formats = {}

    def __init__(self, file, file_offset=None, **kwargs):
        super().__init__(file, file_offset)
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
        total = 0
        table_offset = self['offset']
        file.seek(table_offset)
        end_of_data = table_offset + 4 * math.ceil(self['length'] / 4)
        while file.tell() < end_of_data:
            value = ulong(file)
            if not (self['tag'] == 'head' and file.tell() == table_offset + 12):
                total += value
        checksum = total % 2**32
        assert checksum == self['checkSum']


from .required import HmtxTable
from .cff import CompactFontFormat
from . import truetype, gpos, gsub, other


class OpenTypeParser(dict):
    def __init__(self, filename):
        disk_file = open(filename, 'rb')
        file = io.BytesIO(disk_file.read())
        disk_file.close()
        offset_table = OffsetTable(file)
        table_records = OrderedDict()
        for i in range(offset_table['numTables']):
            record = TableRecord(file)
            table_records[record['tag']] = record
        for tag, record in table_records.items():
            record.check_sum(file)

        for tag in ('head', 'hhea', 'cmap', 'maxp', 'name', 'post', 'OS/2'):
            self[tag] = self._parse_table(file, table_records[tag])

        self['hmtx'] = HmtxTable(file, table_records['hmtx']['offset'],
                                 self['hhea']['numberOfHMetrics'],
                                 self['maxp']['numGlyphs'])
        try:
            self['CFF'] = CompactFontFormat(file,
                                            table_records['CFF']['offset'])
        except KeyError:
            self['loca'] = truetype.LocaTable(file,
                                              table_records['loca']['offset'],
                                              self['head']['indexToLocFormat'],
                                              self['maxp']['numGlyphs'])
            self['glyf'] = truetype.GlyfTable(file,
                                              table_records['glyf']['offset'],
                                              self['loca'])
        for tag in ('kern', 'GPOS', 'GSUB'):
            if tag in table_records:
                self[tag] = self._parse_table(file, table_records[tag])

    def _parse_table(self, file, table_record):
        for cls in recursive_subclasses(OpenTypeTable):
            if cls.tag == table_record['tag']:
                return cls(file, table_record['offset'])
