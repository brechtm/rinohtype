# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct

from .parse import OpenTypeTable, MultiFormatTable, Record
from .parse import byte, ushort, short, ulong, fixed, fword, ufword, uint24
from .parse import longdatetime, string, array, indirect, context_array, Packed
from .macglyphs import MAC_GLYPHS
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

    @property
    def bold(self):
        return bool(self['macStyle'] & MACSTYLE_BOLD)

    @property
    def italic(self):
        return bool(self['macStyle'] & MACSTYLE_ITALIC)

    @property
    def condensed(self):
        return bool(self['macStyle'] & MACSTYLE_CONDENSED)

    @property
    def extended(self):
        return bool(self['macStyle'] & MACSTYLE_EXTENDED)


MACSTYLE_BOLD = 0x1
MACSTYLE_ITALIC = 0x2
MACSTYLE_UNDERLINE = 0x4
MACSTYLE_OUTLINE = 0x8
MACSTYLE_SHADOW = 0x10
MACSTYLE_CONDENSED = 0x20
MACSTYLE_EXTENDED = 0x40


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

    @property
    def italic(self):
        return bool(self['fsSelection'] & FSSELECTION_ITALIC)

    @property
    def bold(self):
        return bool(self['fsSelection'] & FSSELECTION_BOLD)

    @property
    def regular(self):
        return bool(self['fsSelection'] & FSSELECTION_REGULAR)

    @property
    def oblique(self):
        return bool(self['fsSelection'] & FSSELECTION_OBLIQUE)


FSSELECTION_ITALIC = 0x1
FSSELECTION_UNDERSCORE = 0x2
FSSELECTION_NEGATIVE = 0x4
FSSELECTION_OUTLINED = 0x8
FSSELECTION_STRIKEOUT = 0x10
FSSELECTION_BOLD = 0x20
FSSELECTION_REGULAR = 0x40
FSSELECTION_USE_TYPO_METRICS = 0x80
FSSELECTION_WWS = 0x100
FSSELECTION_OBLIQUE = 0x200


class PostTable(MultiFormatTable):
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
    formats = {2.0: [('numberOfGlyphs', ushort),
                     ('glyphNameIndex', context_array(ushort,
                                                      'numberOfGlyphs'))]}

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        self.names = []
        if self['version'] == 2.0:
            num_new_glyphs = max(self['glyphNameIndex']) - 257
            names = []
            for i in range(num_new_glyphs):
                names.append(self._read_pascal_string(file))
            for index in self['glyphNameIndex']:
                if index < 258:
                    name = MAC_GLYPHS[index]
                else:
                    name = names[index - 258]
                self.names.append(name)
        elif self['version'] != 3.0:
            raise NotImplementedError

    def _read_pascal_string(self, file):
        length = byte(file)
        return struct.unpack('>{}s'.format(length),
                             file.read(length))[0].decode('ascii')


class NameRecord(Record):
    entries = [('platformID', ushort),
               ('encodingID', ushort),
               ('languageID', ushort),
               ('nameID', ushort),
               ('length', ushort),
               ('offset', ushort)]


class LangTagRecord(Record):
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


class SubHeader(OpenTypeTable):
    entries = [('firstCode', ushort),
               ('entryCount', ushort),
               ('idDelta', short),
               ('idRangeOffset', ushort)]


class CmapGroup(OpenTypeTable):
    entries = [('startCharCode', ulong),
               ('endCharCode', ulong),
               ('startGlyphID', ulong)]


class VariationSelectorRecord(OpenTypeTable):
    entries = [('varSelector', uint24),
               ('defaultUVSOffset', ulong),
               ('nonDefaultUVSOffset', ulong)]


class CmapSubtable(MultiFormatTable):
    entries = [('format', ushort)]
    formats = {0: # Byte encoding table
                  [('length', ushort),
                   ('language', ushort),
                   ('glyphIdArray', array(byte, 256))],
               2: # High-byte mapping through table
                  [('length', ushort),
                   ('language', ushort),
                   ('subHeaderKeys', array(ushort, 256))],
               4: # Segment mapping to delta values
                  [('length', ushort),
                   ('language', ushort),
                   ('segCountX2', ushort),
                   ('searchRange', ushort),
                   ('entrySelector', ushort),
                   ('rangeShift', ushort),
                   ('endCount', context_array(ushort, 'segCountX2',
                                              multiplier=0.5)),
                   (None, ushort),
                   ('startCount', context_array(ushort, 'segCountX2',
                                                multiplier=0.5)),
                   ('idDelta', context_array(short, 'segCountX2',
                                             multiplier=0.5)),
                   ('idRangeOffset', context_array(ushort, 'segCountX2',
                                                   multiplier=0.5))],
               6: # Trimmed table mapping
                  [('length', ushort),
                   ('language', ushort),
                   ('firstCode', ushort),
                   ('entryCount', ushort),
                   ('glyphIdArray', context_array(ushort, 'entryCount'))],
               8: # Mixed 16-bit and 32-bit coverage
                  [(None, ushort),
                   ('length', ulong),
                   ('language', ulong),
                   ('is32', array(byte, 8192)),
                   ('nGroups', ulong),
                   ('group', context_array(CmapGroup, 'nGroups'))],
              10: # Trimmed array
                  [(None, ushort),
                   ('length', ulong),
                   ('language', ulong),
                   ('startCharCode', ulong),
                   ('numchars', ulong),
                   ('glyphs', context_array(ushort, 'numChars'))],
              12: # Segmented coverage
                  [(None, ushort),
                   ('length', ulong),
                   ('language', ulong),
                   ('nGroups', ulong),
                   ('groups', context_array(CmapGroup, 'nGroups'))],
              13: # Many-to-one range mappings
                  [(None, ushort),
                   ('length', ulong),
                   ('language', ulong),
                   ('nGroups', ulong),
                   ('groups', context_array(CmapGroup, 'nGroups'))],
              14: # Unicode Variation Sequences
                  [('length', ulong),
                   ('numVarSelectorRecords', ulong),
                   ('varSelectorRecord', context_array(VariationSelectorRecord,
                                                       'numVarSelectorRecords'))]}

    # TODO
##    formats[99] = [('bla', ushort)]
##    def _format_99_init(self):
##        pass

    def __init__(self, file, file_offset=None, **kwargs):
        # TODO: detect already-parsed table (?)
        super().__init__(file, file_offset)
        # TODO: create format-dependent lookup function instead of storing
        #       everything in a dict (not efficient for format 13 subtables fe)
        if self['format'] == 0:
            indices = array(byte, 256)(file)
            out = {i: index for i, index in enumerate(self['glyphIdArray'])}
        elif self['format'] == 2:
            raise NotImplementedError
        elif self['format'] == 4:
            seg_count = self['segCountX2'] >> 1
            self['glyphIdArray'] = array(ushort, self['length'])(file)
            segments = zip(self['startCount'], self['endCount'],
                           self['idDelta'], self['idRangeOffset'])
            out = {}
            for i, (start, end, delta, range_offset) in enumerate(segments):
                if i == seg_count - 1:
                    assert end == 0xFFFF
                    break
                if range_offset > 0:
                    for j, code in enumerate(range(start, end + 1)):
                        index = (range_offset >> 1) - seg_count + i + j
                        out[code] = self['glyphIdArray'][index]
                else:
                    for code in range(start, end + 1):
                        out[code] = (code + delta) % 2**16
        elif self['format'] == 6:
            out = {code: index for code, index in
                   zip(range(self['firstCode'],
                             self['firstCode'] + self['entryCount']),
                       self['glyphIdArray'])}
        elif self['format'] == 12:
            out = {}
            for group in self['groups']:
                codes = range(group['startCharCode'], group['endCharCode'] + 1)
                segment = {code: group['startGlyphID'] + index
                           for index, code in enumerate(codes)}
                out.update(segment)
        elif self['format'] == 13:
            out = {}
            for group in self['groups']:
                codes = range(group['startCharCode'], group['endCharCode'] + 1)
                segment = {code: group['startGlyphID'] for code in codes}
                out.update(segment)
        else:
            raise NotImplementedError
        self.mapping = out


class CmapRecord(Record):
    entries = [('platformID', ushort),
               ('encodingID', ushort),
               ('subtable', indirect(CmapSubtable, offset_reader=ulong))]


class CmapTable(OpenTypeTable):
    tag = 'cmap'
    entries = [('version', ushort),
               ('numTables', ushort),
               ('encodingRecord', context_array(CmapRecord, 'numTables'))]

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        for record in self['encodingRecord']:
            key = (record['platformID'], record['encodingID'])
            self[key] = record['subtable']
