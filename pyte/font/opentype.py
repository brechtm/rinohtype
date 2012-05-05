
import ctypes, hashlib, math, struct

from . import Font
from .style import MEDIUM, UPRIGHT, NORMAL, ITALIC
from datetime import datetime, timedelta



# using the names and datatypes from the OpenType specification
# http://www.microsoft.com/typography/otspec/

byte = lambda file: grab(file, 'B')[0]
char = lambda file: grab(file, 'b')[0]
ushort = lambda file: grab(file, 'H')[0]
short = lambda file: grab(file, 'h')[0]
ulong = lambda file: grab(file, 'L')[0]
long = lambda file: grab(file, 'l')[0]
fword = short
ufword = ushort
longdatetime = lambda file: grab_datetime(file)

string = lambda file: grab(file, '4s')[0].decode('ascii')

def fixed(file):
    version, = grab(file, 'L')
    return version / 2**16

def array(reader, length):
    return lambda file: [reader(file) for i in range(length)]


head = [('version', fixed),
        ('fontRevision', fixed),
        ('checkSumAdjustment', ulong),
        ('magicNumber', ulong),
        ('flags', ushort),
        ('unitsPerEm', ushort),
        ('created', longdatetime),
        ('modified', longdatetime),
        ('xMin', short),
        ('yMin', short),
        ('xMax', short),
        ('yMax', short),
        ('macStyle', ushort),
        ('lowestRecPPEM', ushort),
        ('fontDirectionHint', short),
        ('indexToLocFormat', short),
        ('glyphDataFormat', short)]

hhea = [('version', fixed),
        ('Ascender', fword),
        ('Descender', fword),
        ('LineGap', fword),
        ('advanceWidthMax', ufword),
        ('minLeftSideBearing', fword),
        ('minRightSideBearing', fword),
        ('xMaxExtent', fword),
        ('caretSlopeRise', short),
        ('caretSlopeRun', short),
        ('caretOffset', short),
        (None, short),
        (None, short),
        (None, short),
        (None, short),
        ('metricDataFormat', short),
        ('numberOfHMetrics', ushort)]

maxp = [('version', fixed),
        ('numGlyphs', ushort),
        ('maxPoints', ushort),
        ('maxContours', ushort),
        ('maxCompositePoints', ushort),
        ('maxCompositeContours', ushort),
        ('maxZones', ushort),
        ('maxTwilightPoints', ushort),
        ('maxStorage', ushort),
        ('maxFunctionDefs', ushort),
        ('maxInstructionDefs', ushort),
        ('maxStackElements', ushort),
        ('maxSizeOfInstructions', ushort),
        ('maxComponentElements', ushort),
        ('maxComponentDepth', ushort)]

os_2 = [('version', ushort),
        ('xAvgCharWidth', short),
        ('usWeightClass', ushort),
        ('usWidthClass', ushort),
        ('fsType', ushort),
        ('ySubscriptXSize', short),
        ('ySubscriptYSize', short),
        ('ySubscriptXOffset', short),
        ('ySubscriptYOffset', short),
        ('ySuperscriptXSize', short),
        ('ySuperscriptYSize', short),
        ('ySuperscriptXOffset', short),
        ('ySuperscriptYOffset', short),
        ('yStrikeoutSize', short),
        ('yStrikeoutPosition', short),
        ('sFamilyClass', short),
        ('panose', array(byte, 10)),
        ('ulUnicodeRange1', ulong),
        ('ulUnicodeRange2', ulong),
        ('ulUnicodeRange3', ulong),
        ('ulUnicodeRange4', ulong),
        ('achVendID', string),
        ('fsSelection', ushort),
        ('usFirstCharIndex', ushort),
        ('usLastCharIndex', ushort),
        ('sTypoAscender', short),
        ('sTypoDescender', short),
        ('sTypoLineGap', short),
        ('usWinAscent', ushort),
        ('usWinDescent', ushort),
        ('ulCodePageRange1', ulong),
        ('ulCodePageRange2', ulong),
        ('sxHeight', short),
        ('sCapHeight', short),
        ('usDefaultChar', ushort),
        ('usBreakChar', ushort),
        ('usMaxContext', ushort)]

post = [('version', fixed),
        ('italicAngle', fixed),
        ('underlinePosition', fword),
        ('underlineThickness', fword),
        ('isFixedPitch', ulong),
        ('minMemType42', ulong),
        ('maxMemType42', ulong),
        ('minMemType1', ulong),
        ('maxMemType1', ulong)]

name = [('format', ushort),
        ('count', ushort),
        ('stringOffset', ushort)]

name_record = [('platformID', ushort),
               ('encodingID', ushort),
               ('languageID', ushort),
               ('nameID', ushort),
               ('length', ushort),
               ('offset', ushort)]

lang_tag_record = [('length', ushort),
                   ('offset', ushort)]

cmap = [('version', ushort),
        ('numTables', ushort)]

cmap_record = [('platformID', ushort),
               ('encodingID', ushort),
               ('offset', ulong)]

cmap_4 = [('segCountX2', ushort),
          ('searchRange', ushort),
          ('entrySelector', ushort),
          ('rangeShift', ushort)]


class OpenTypeFont(Font, dict):
    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.metrics = None
        self.encoding = None
        super().__init__(weight, slant, width)
        file = open(filename, 'rb')
        offset_table = self.parse_offset_table(file)
        file.close()

##    @property
##    def postscript_name(self):
##        return self.metrics['FontMetrics']['FontName']

    def has_glyph(self, name):
        return name in self.metrics.glyphs

    def parse_offset_table(self, file):
        tup = grab(file, '4sHHHH')
        version, num_tables, search_range, entry_selector, range_shift = tup
        tables = {}
        for i in range(num_tables):
            tag, checksum, offset, length = grab(file, '4sLLL')
            tables[tag.decode('ascii')] = offset, length, checksum
        for tag, (offset, length, checksum) in tables.items():
            cs = calculate_checksum(file, offset, length, tag=='head')
            assert cs == checksum
        self.head = self.parse_table(head, file, tables['head'][0])
        self.post = self.parse_table(post, file, tables['post'][0])
        self.hhea = self.parse_table(hhea, file, tables['hhea'][0])
        self.maxp = self.parse_maxp(file, tables['maxp'][0])
        self.hmtx = self.parse_hmtx(file, tables['hmtx'][0],
                                    self.hhea['numberOfHMetrics'],
                                    self.maxp['numGlyphs'])
        self.os_2 = self.parse_table(os_2, file, tables['OS/2'][0])
        self.name = self.parse_name(file, tables['name'][0])
        self.cmap = self.parse_cmap(file, tables['cmap'][0])

    def parse_table(self, table, file, offset):
        out = {}
        file.seek(offset)
        for key, reader in table:
            value = reader(file)
            if key is not None:
                out[key] = value
        return out

    def parse_maxp(self, file, offset):
        out = {}
        file.seek(offset)
        for i, (key, reader) in enumerate(maxp):
            if key == 'maxPoints' and out['version'] != 1.0:
                break
            out[key] = reader(file)
        return out

    def parse_hmtx(self, file, offset, number_of_h_metrics, num_glyphs):
        out = []
        file.seek(offset)
        for i in range(number_of_h_metrics):
            advance_width, left_side_bearing = grab(file, 'Hh')
            out.append((advance_width, left_side_bearing))
        for i in range(num_glyphs - number_of_h_metrics):
            left_side_bearing, = grab(file, 'h')
            out.append((advance_width, left_side_bearing))
        return out

    def parse_name(self, file, offset):
        table = self.parse_table(name, file, offset)
        records = []
        for i in range(table['count']):
            record = self.parse_table(name_record, file, file.tell())
            records.append(record)
        if table['format'] == 1:
            raise NotImplementedError
        data_offset = file.tell()
        for record in records:
            file.seek(data_offset + record['offset'])
            data = file.read(record['length'])
            # TODO: decode according to platform and encoding
            record['data'] = data
        table['records'] = records
        return table

    def parse_cmap(self, file, offset):
        table = self.parse_table(cmap, file, offset)
        records = []
        for i in range(table['numTables']):
            record = self.parse_table(cmap_record, file, file.tell())
            records.append(record)
        for record in records:
            record_offset = offset + record['offset']
            file.seek(record_offset)
            table_format = ushort(file)
            if table_format in (8, 10, 12, 13):
                reserved = ushort(file)
            length = ushort(file)
            if table_format != 14:
                language = ushort(file),
            # TODO: detect already-parsed table
            if table_format == 0: # byte encoding table
                out = {zip(range(256), array(byte, 256))(file)}
            elif table_format == 2: # high-byte mapping through table
                raise NotImplementedError
            elif table_format == 4: # segment mapping to delta values
                meta = self.parse_table(cmap_4, file, file.tell())
                seg_count = meta['segCountX2'] >> 1
                end_count = array(ushort, seg_count)(file)
                reserved_pad = ushort(file)
                start_count = array(ushort, seg_count)(file)
                id_delta = array(short, seg_count)(file)
                id_range_offset = array(ushort, seg_count)(file)
                glyph_id_array_length = (record_offset + length - file.tell())
                glyph_id_array = array(ushort, glyph_id_array_length >> 1)(file)
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
                first_code, entry_count = ushort(file), ushort(file)
                out = {code: index for code, index in
                       zip(range(first_code, first_code + entry_count),
                           array(ushort, entry_count)(file))}
            else:
                raise NotImplementedError('table format {}', table_format)
            record['map'] = out
        table['records'] = records
        return table


def grab(file, data_format):
    data = file.read(struct.calcsize(data_format))
    return struct.unpack('>' + data_format, data)


def grab_datetime(file):
    return datetime(1904, 1, 1, 12) + timedelta(seconds=grab(file, 'Q')[0])


def calculate_checksum(file, offset, length, head=False):
    tmp = 0
    file.seek(offset)
    end_of_data = offset + 4 * math.ceil(length / 4)
    while file.tell() < end_of_data:
        uint32 = grab(file, 'L')[0]
        if not (head and file.tell() == offset + 12):
            tmp += uint32
    return tmp % 2**32


##class CMapTable(object):
##    def __init__(self):
##        pass
##
##    def __getitem__(self, index):
##        raise NotImplementedError
##
##
##class CMapTable4(CMapTable):
##    def __init__(self):
##        pass
##
##    def __getitem__(self, index):
##        raise NotImplementedError
