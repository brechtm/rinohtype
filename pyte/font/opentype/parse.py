
import hashlib, math, io, struct
from datetime import datetime, timedelta
from collections import OrderedDict

from ...util import recursive_subclasses
from .cff import CompactFontFormat


def create_reader(data_format):
    data_struct = struct.Struct('>' + data_format)
    return lambda file: data_struct.unpack(file.read(data_struct.size))[0]


# using the names and datatypes from the OpenType specification
# http://www.microsoft.com/typography/otspec/
byte = create_reader('B')
char = create_reader('b')
ushort = create_reader('H')
short = create_reader('h')
ulong = create_reader('L')
long = create_reader('l')
fixed = lambda file: ulong(file) / 2**16
int16 = fword = short
uint16 = ufword = ushort
string = lambda file: string._grabber(file).decode('ascii').strip()
string._grabber = create_reader('4s')
tag = string
glyph_id = uint16
offset = uint16

def longdatetime(file):
    return longdatetime._epoch + timedelta(seconds=longdatetime._grabber(file))

longdatetime._epoch = datetime(1904, 1, 1, 12)
longdatetime._grabber = create_reader('Q')


def array(reader, length):
    return lambda file: [reader(file) for i in range(length)]


def indirect(reader):
    def read_and_restore_file_position(not_used, file, file_offset):
        indirect_offset = offset(file)
        restore_position = file.tell()
        result = reader(file, file_offset + indirect_offset)
        file.seek(restore_position)
        return result
    return read_and_restore_file_position


def context_array(reader, count_key):
    return lambda table, file, not_used: array(reader, table[count_key])(file)


def indirect_array(entry_type, count_key):
    def reader_function(table, file, file_offset):
        offsets = array(offset, table[count_key])(file)
        return [entry_type(file, file_offset + entry_offset)
                for entry_offset in offsets]
    return reader_function


class Packed(OrderedDict):
    reader = None
    fields = []

    def __init__(self, file):
        super().__init__(self)
        self.value = self.__class__.reader(file)
        for name, mask, processor in self.fields:
            self[name] = processor(self.value & mask)


class OpenTypeTable(OrderedDict):
    tag = None
    entries = []

    def __init__(self, file, file_offset=None):
        super().__init__()
        if file_offset is not None:
            file.seek(file_offset)
        self.parse(file, file_offset, self.entries)

    def parse(self, file, file_offset, entries):
        for key, reader in entries:
            try:
                value = reader(file)
            except TypeError: # reader requires the context
                value = reader(self, file, file_offset)
            if key is not None:
                self[key] = value


class MultiFormatTable(OpenTypeTable):
    formats = {}

    def __init__(self, file, file_offset=None):
        super().__init__(file, file_offset)
        table_format = self[self.entries[0][0]]
        if table_format in self.formats:
            self.parse(file, file_offset, self.formats[table_format])


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


from .tables import HmtxTable


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
        self['CFF'] = CompactFontFormat(file, table_records['CFF']['offset'])
        for tag in ('kern', 'GPOS', 'GSUB'):
            if tag in table_records:
                self[tag] = self._parse_table(file, table_records[tag])

    def _parse_table(self, file, table_record):
        for cls in recursive_subclasses(OpenTypeTable):
            if cls.tag == table_record['tag']:
                return cls(file, table_record['offset'])
