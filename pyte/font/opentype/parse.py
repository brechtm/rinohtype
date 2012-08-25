
import hashlib, math, struct
from datetime import datetime, timedelta


def grab(file, data_format):
    data = file.read(struct.calcsize(data_format))
    return struct.unpack('>' + data_format, data)


def grab_datetime(file):
    return datetime(1904, 1, 1, 12) + timedelta(seconds=grab(file, 'Q')[0])


# using the names and datatypes from the OpenType specification
# http://www.microsoft.com/typography/otspec/

byte = lambda file: grab(file, 'B')[0]
char = lambda file: grab(file, 'b')[0]
ushort = lambda file: grab(file, 'H')[0]
short = lambda file: grab(file, 'h')[0]
ulong = lambda file: grab(file, 'L')[0]
long = lambda file: grab(file, 'l')[0]
fixed = lambda file: grab(file, 'L')[0] / 2**16
fword = short
ufword = ushort
longdatetime = lambda file: grab_datetime(file)
string = lambda file: grab(file, '4s')[0].decode('ascii')


def array(reader, length):
    return lambda file: [reader(file) for i in range(length)]


from .tables import HEAD, HHEA, MAXP, OS_2, POST, NAME, NAME_RECORD
from .tables import LANG_TAG_RECORD, CMAP, CMAP_RECORD, CMAP_4


class OpenTypeParser(object):
    def __init__(self, filename):
        self.file = open(filename, 'rb')
        self.parse_tables()
        self.file.close()

    def calculate_checksum(self, offset, length, head=False):
        tmp = 0
        self.file.seek(offset)
        end_of_data = offset + 4 * math.ceil(length / 4)
        while self.file.tell() < end_of_data:
            uint32 = grab(self.file, 'L')[0]
            if not (head and self.file.tell() == offset + 12):
                tmp += uint32
        return tmp % 2**32

    def parse_tables(self):
        tup = grab(self.file, '4sHHHH')
        version, num_tables, search_range, entry_selector, range_shift = tup
        tables = {}
        for i in range(num_tables):
            tag, checksum, offset, length = grab(self.file, '4sLLL')
            tables[tag.decode('ascii')] = offset, length, checksum
        for tag, (offset, length, checksum) in tables.items():
            cs = self.calculate_checksum(offset, length, tag=='head')
            assert cs == checksum
        self.head = self.parse_table(HEAD, tables['head'][0])
        self.post = self.parse_table(POST, tables['post'][0])
        if self.post['version'] != 3.0:
            raise NotImplementedError()
        self.hhea = self.parse_table(HHEA, tables['hhea'][0])
        self.maxp = self.parse_maxp(tables['maxp'][0])
        self.hmtx = self.parse_hmtx(tables['hmtx'][0],
                                    self.hhea['numberOfHMetrics'],
                                    self.maxp['numGlyphs'])
        self.os_2 = self.parse_table(OS_2, tables['OS/2'][0])
        self.name = self.parse_name(tables['name'][0])
        self.cmap = self.parse_cmap(tables['cmap'][0])

    def parse_table(self, table, offset):
        out = {}
        self.file.seek(offset)
        for key, reader in table:
            value = reader(self.file)
            if key is not None:
                out[key] = value
        return out

    def parse_maxp(self, offset):
        out = {}
        self.file.seek(offset)
        for i, (key, reader) in enumerate(MAXP):
            if key == 'maxPoints' and out['version'] != 1.0:
                break
            out[key] = reader(self.file)
        return out

    def parse_hmtx(self, offset, number_of_h_metrics, num_glyphs):
        out = []
        self.file.seek(offset)
        for i in range(number_of_h_metrics):
            advance_width, left_side_bearing = grab(self.file, 'Hh')
            out.append((advance_width, left_side_bearing))
        for i in range(num_glyphs - number_of_h_metrics):
            left_side_bearing, = grab(self.file, 'h')
            out.append((advance_width, left_side_bearing))
        return out

    def parse_name(self, offset):
        table = self.parse_table(NAME, offset)
        records = []
        for i in range(table['count']):
            record = self.parse_table(NAME_RECORD, self.file.tell())
            records.append(record)
        if table['format'] == 1:
            raise NotImplementedError
        data_offset = self.file.tell()
        out = {}
        for record in records:
            self.file.seek(data_offset + record['offset'])
            data = self.file.read(record['length'])
            # TODO: decode according to platform and encoding
            if record['platformID'] == PLATFORM_WINDOWS:
                out[record['nameID']] = decode(record['platformID'],
                                               record['encodingID'], data)
        return out

    def parse_cmap(self, offset):
        table = self.parse_table(CMAP, offset)
        records = []
        for i in range(table['numTables']):
            record = self.parse_table(CMAP_RECORD, self.file.tell())
            records.append(record)
        for record in records:
            record_offset = offset + record['offset']
            self.file.seek(record_offset)
            table_format = ushort(self.file)
            if table_format in (8, 10, 12, 13):
                reserved = ushort(self.file)
            length = ushort(self.file)
            if table_format != 14:
                language = ushort(self.file),
            # TODO: detect already-parsed table
            if table_format == 0: # byte encoding table
                out = {zip(range(256), array(byte, 256))(self.file)}
            elif table_format == 2: # high-byte mapping through table
                raise NotImplementedError
            elif table_format == 4: # segment mapping to delta values
                meta = self.parse_table(CMAP_4, self.file.tell())
                seg_count = meta['segCountX2'] >> 1
                end_count = array(ushort, seg_count)(self.file)
                reserved_pad = ushort(self.file)
                start_count = array(ushort, seg_count)(self.file)
                id_delta = array(short, seg_count)(self.file)
                id_range_offset = array(ushort, seg_count)(self.file)
                glyph_id_array_length = (record_offset + length
                                            - self.file.tell())
                glyph_id_array = array(ushort,
                                       glyph_id_array_length >> 1)(self.file)
                segments = zip(start_count, end_count, id_delta,
                               id_range_offset)
                out = {}
                for i, (start, end, delta, range_offset) in enumerate(segments):
                    if i == seg_count - 1:
                        assert end == 0xFFFF
                        break
                    if range_offset > 0:
                        for j, code in enumerate(range(start, end + 1)):
                            index = (range_offset >> 1) - seg_count + i + j
                            out[code] = glyph_id_array[index]
                    else:
                        for code in range(start, end + 1):
                            out[code] = (code + delta) % 2**16
            elif table_format == 6: # trimmed table mapping
                first_code, entry_count = ushort(self.file), ushort(self.file)
                out = {code: index for code, index in
                       zip(range(first_code, first_code + entry_count),
                           array(ushort, entry_count)(self.file))}
            else:
                raise NotImplementedError('table format {}', table_format)
            record['map'] = out
        table['records'] = records
        return table


PLATFORM_UNICODE = 0
PLATFORM_MACINTOSH = 1
PLATFORM_ISO = 2
PLATFORM_WINDOWS = 3
PLATFORM_CUSTOM = 4

NAME_COPYRIGHT = 0
NAME_FAMILTY = 1
NAME_SUBFAMILY = 2
NAME_UID = 3
NAME_FULL = 4
NAME_VERSION = 5
NAME_PS_NAME = 6
NAME_TRADEMARK = 7
NAME_MANUFACTURER = 8
NAME_DESIGNER = 9
NAME_DESCRIPTION = 10
NAME_VENDOR_URL = 11
NAME_DESIGNER_URL = 12
NAME_LICENSE = 13
NAME_LICENSE_URL = 14
NAME_PREFERRED_FAMILY = 16
NAME_PREFERRED_SUBFAMILY = 17
# ...


def decode(platform_id, encoding_id, data):
    try:
        return data.decode(encodings[platform_id][encoding_id])
    except KeyError:
        raise NotImplementedError()


encodings = {}

encodings[PLATFORM_UNICODE] = {}

UNICODE_1_0 = 0
UNICODE_1_1 = 1
UNICODE_ISO_IEC_10646 = 2
UNICODE_2_0_BMP = 3
UNICODE_2_0_FULL = 4
UNICODE_VAR_SEQ = 5
UNICODE_FULL = 6

encodings[PLATFORM_MACINTOSH] = {}

encodings[PLATFORM_ISO] = {}

ISO_ASCII = 0
ISO_10646 = 1
ISO_8859_1 = 2

encodings[PLATFORM_WINDOWS] = {1: 'utf_16_be',
                               2: 'cp932',
                               3: 'gbk',
                               4: 'cp950',
                               5: 'euc_kr',
                               6: 'johab',
                               10: 'utf_32_be'}
