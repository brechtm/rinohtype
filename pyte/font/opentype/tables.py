
from collections import OrderedDict

from ...util import recursive_subclasses
from .parse import grab
from .parse import byte, char, ushort, short, ulong, long, fixed
from .parse import fword, ufword, longdatetime, string, array, offset, Packed
from .parse import PLATFORM_WINDOWS, decode


def parse_table(tag, file, file_offset):
    for cls in recursive_subclasses(OpenTypeTable):
        if cls.tag == tag:
            return cls(file, file_offset)


def context_array(reader, count_key):
    return lambda table, file, not_used: array(reader, table[count_key])(file)


def offset_array(entry_type, count_key):
    def reader_function(table, file, file_offset):
        offsets = array(offset, table[count_key])(file)
        return [entry_type(file, file_offset + entry_offset)
                for entry_offset in offsets]
    return reader_function


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


class HeadTable(OpenTypeTable):
    """Font header"""
    tag = 'head'
    entries = [('version', fixed),
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


class HheaTable(OpenTypeTable):
    """Horizontal header"""
    tag = 'hhea'
    entries = [('version', fixed),
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


class HmtxTable(OpenTypeTable):
    """Horizontal metrics"""
    tag = 'htmx'

    def __init__(self, file, offset, number_of_h_metrics, num_glyphs):
        super().__init__(file, offset)
        # TODO: rewrite using context_array ?
        file.seek(offset)
        advance_widths = []
        left_side_bearings = []
        for i in range(number_of_h_metrics):
            advance_width, lsb = grab(file, 'Hh')
            advance_widths.append(advance_width)
            left_side_bearings.append(lsb)
        for i in range(num_glyphs - number_of_h_metrics):
            lsb, = grab(file, 'h')
            advance_widths.append(advance_width)
            left_side_bearings.append(lsb)
        self['advanceWidth'] = advance_widths
        self['leftSideBearing'] = left_side_bearings


class MaxpTable(MultiFormatTable):
    """Maximum profile"""
    tag = 'maxp'
    entries = [('version', fixed),
               ('numGlyphs', ushort),
               ('maxPoints', ushort)]
    format_entries = {1.0: [('maxContours', ushort),
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
                            ('maxComponentDepth', ushort)]}


class OS2Table(OpenTypeTable):
    """OS/2 and Windows specific metrics"""
    tag = 'OS/2'
    entries = [('version', ushort),
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


class PostTable(OpenTypeTable):
    """PostScript information"""
    tag = 'post'
    entries = [('version', fixed),
               ('italicAngle', fixed),
               ('underlinePosition', fword),
               ('underlineThickness', fword),
               ('isFixedPitch', ulong),
               ('minMemType42', ulong),
               ('maxMemType42', ulong),
               ('minMemType1', ulong),
               ('maxMemType1', ulong)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        if self['version'] != 3.0:
            raise NotImplementedError()


class NameRecord(OpenTypeTable):
    entries = [('platformID', ushort),
               ('encodingID', ushort),
               ('languageID', ushort),
               ('nameID', ushort),
               ('length', ushort),
               ('offset', ushort)]


class NameTable(OpenTypeTable):
    """Naming table"""
    tag = 'name'
    entries = [('format', ushort),
               ('count', ushort),
               ('stringOffset', ushort)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        records = []
        for i in range(self['count']):
            record = NameRecord(file, file.tell())
            records.append(record)
        if self['format'] == 1:
            raise NotImplementedError
        data_offset = file.tell()
        for record in records:
            file.seek(data_offset + record['offset'])
            data = file.read(record['length'])
            # TODO: decode according to platform and encoding
            if record['platformID'] == PLATFORM_WINDOWS:
                self[record['nameID']] = decode(record['platformID'],
                                                record['encodingID'], data)


class CmapRecord(OpenTypeTable):
    entries = [('platformID', ushort),
               ('encodingID', ushort),
               ('offset', ulong)]


class Cmap4Record(OpenTypeTable):
    entries = [('segCountX2', ushort),
               ('searchRange', ushort),
               ('entrySelector', ushort),
               ('rangeShift', ushort)]


class CmapTable(OpenTypeTable):
    tag = 'cmap'
    entries = [('version', ushort),
               ('numTables', ushort)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        records = []
        for i in range(self['numTables']):
            record = CmapRecord(file, file.tell())
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
                indices = array(byte, 256)(file)
                out = {i: index for i, index in enumerate(indices)}
            elif table_format == 2: # high-byte mapping through table
                raise NotImplementedError
            elif table_format == 4: # segment mapping to delta values
                meta = Cmap4Record(file, file.tell())
                seg_count = meta['segCountX2'] >> 1
                end_count = array(ushort, seg_count)(file)
                reserved_pad = ushort(file)
                start_count = array(ushort, seg_count)(file)
                id_delta = array(short, seg_count)(file)
                id_range_offset = array(ushort, seg_count)(file)
                glyph_id_array_length = (record_offset + length
                                            - file.tell())
                glyph_id_array = array(ushort,
                                       glyph_id_array_length >> 1)(file)
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
            key = (record['platformID'], record['encodingID'])
            self[key] = out


LANG_TAG_RECORD = [('length', ushort),
                   ('offset', ushort)]


class KerningCoverage(Packed):
    reader = ushort
    fields = [('horizontal', 0b0001, bool),
              ('minimum', 0b0010, bool),
              ('cross-stream', 0b0100, bool),
              ('override', 0b1000, bool),
              ('format', 0xF0, int),]


class KernSubTable(OpenTypeTable):
    """Kerning subtable"""
    entries = [('version', ushort),
               ('length', ushort),
               ('coverage', KerningCoverage)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        if self['coverage']['format'] == 0:
            self.pairs = {}
            (n_pairs, search_range,
             entry_selector, range_shift) = array(ushort, 4)(file)
            for i in range(n_pairs):
                left, right, value = ushort(file), ushort(file), fword(file)
                left_dict = self.pairs.setdefault(left, {})
                left_dict[right] = value
        else:
            raise NotImplementedError


class KernTable(OpenTypeTable):
    """Kerning table (only for TrueType outlines)"""
    tag = 'kern'
    entries = [('version', ushort),
               ('nTables', ushort)]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        for i in range(self['nTables']):
            subtable = KernSubTable(file, file.tell())
            self[subtable['coverage']['format']] = subtable


from . import gpos
