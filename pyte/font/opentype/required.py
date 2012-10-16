
from .parse import OpenTypeTable, MultiFormatTable
from .parse import byte, ushort, short, ulong, fixed, fword, ufword
from .parse import longdatetime, string, array, context_array, Packed
from . import ids


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

    @property
    def bounding_box(self):
        return (self['xMin'], self['yMin'], self['xMax'], self['yMax'])


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

    def __init__(self, file, file_offset, number_of_h_metrics, num_glyphs):
        super().__init__(file, file_offset)
        # TODO: rewrite using context_array ?
        file.seek(file_offset)
        advance_widths = []
        left_side_bearings = []
        for i in range(number_of_h_metrics):
            advance_width, lsb = ushort(file), short(file)
            advance_widths.append(advance_width)
            left_side_bearings.append(lsb)
        for i in range(num_glyphs - number_of_h_metrics):
            lsb = short(file)
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


class LangTagRecord(OpenTypeTable):
    entries = [('length', ushort),
               ('offset', ushort)]


class NameTable(MultiFormatTable):
    """Naming table"""
    tag = 'name'
    entries = [('format', ushort),
               ('count', ushort),
               ('stringOffset', ushort),
               ('nameRecord', context_array(NameRecord, 'count'))]
    formats = {1: [('langTagCount', ushort),
                   ('langTagRecord', context_array(LangTagRecord,
                                                   'langTagCount'))]}

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        if self['format'] == 1:
            raise NotImplementedError
        string_offset = file_offset + self['stringOffset']
        self.strings = {}
        for record in self['nameRecord']:
            file.seek(string_offset + record['offset'])
            data = file.read(record['length'])
            if record['platformID'] in (ids.PLATFORM_UNICODE,
                                        ids.PLATFORM_WINDOWS):
                string = data.decode('utf_16_be')
            elif record['platformID'] == ids.PLATFORM_MACINTOSH:
                # TODO: properly decode according to the specified encoding
                string = data.decode('mac_roman')
            else:
                raise NotImplementedError
            name = self.strings.setdefault(record['nameID'], {})
            platform = name.setdefault(record['platformID'], {})
            platform[record['languageID']] = string


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

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        records = []
        for i in range(self['numTables']):
            record = CmapRecord(file, file.tell())
            records.append(record)
        for record in records:
            record_offset = file_offset + record['offset']
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
                glyph_id_array_length = (record_offset + length - file.tell())
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
