
from .parse import byte, char, ushort, short, ulong, long, fixed
from .parse import fword, ufword, longdatetime, string, array


HEAD = [('version', fixed),
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

HHEA = [('version', fixed),
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

MAXP = [('version', fixed),
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

OS_2 = [('version', ushort),
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

POST = [('version', fixed),
        ('italicAngle', fixed),
        ('underlinePosition', fword),
        ('underlineThickness', fword),
        ('isFixedPitch', ulong),
        ('minMemType42', ulong),
        ('maxMemType42', ulong),
        ('minMemType1', ulong),
        ('maxMemType1', ulong)]

NAME = [('format', ushort),
        ('count', ushort),
        ('stringOffset', ushort)]

NAME_RECORD = [('platformID', ushort),
               ('encodingID', ushort),
               ('languageID', ushort),
               ('nameID', ushort),
               ('length', ushort),
               ('offset', ushort)]

LANG_TAG_RECORD = [('length', ushort),
                   ('offset', ushort)]

CMAP = [('version', ushort),
        ('numTables', ushort)]

CMAP_RECORD = [('platformID', ushort),
               ('encodingID', ushort),
               ('offset', ulong)]

CMAP_4 = [('segCountX2', ushort),
          ('searchRange', ushort),
          ('entrySelector', ushort),
          ('rangeShift', ushort)]
