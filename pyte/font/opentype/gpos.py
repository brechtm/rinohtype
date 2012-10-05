
from .tables import OpenTypeTable, MultiFormatTable, context_array, offset_array
from .parse import fixed, int16, uint16, tag, glyph_id, offset, array, indirect
from .parse import Packed
from .layout import ScriptListTable, FeatureListTable, LookupTable
from .layout import Coverage, ClassDefinition


class GposTable(OpenTypeTable):
    """Glyph positioning table"""
    tag = 'GPOS'
    entries = [('Version', fixed)]

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        script_offset, feature_offset, lookup_offset = array(offset, 3)(file)
        self['ScriptList'] = ScriptListTable(file,
                                             file_offset + script_offset)
        self['FeatureList'] = FeatureListTable(file,
                                               file_offset + feature_offset)
        self['LookupList'] = GposLookupListTable(file,
                                                 file_offset + lookup_offset)


class ValueFormat(Packed):
    reader = uint16
    fields = [('XPlacement', 0x0001, bool),
              ('YPlacement', 0x0002, bool),
              ('XAdvance', 0x0004, bool),
              ('YAdvance', 0x0008, bool),
              ('XPlaDevice', 0x0010, bool),
              ('YPlaDevice', 0x0020, bool),
              ('XAdvDevice', 0x0040, bool),
              ('YAdvDevice', 0x0080, bool)]


# TODO: MultiFormatTable
class PairAdjustmentSubtable(OpenTypeTable):
    entries = [('PosFormat', uint16),
               ('Coverage', indirect(Coverage)),
               ('ValueFormat1', ValueFormat),
               ('ValueFormat2', ValueFormat)]

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        if self['PosFormat'] == 1:
            self['PairSetCount'] = uint16(file)
            pst_reader = (lambda file, file_offset:
                              PairSetTable(file, file_offset,
                                           self['ValueFormat1'],
                                           self['ValueFormat2']))
            self['PairSet'] = (offset_array(pst_reader, 'PairSetCount')
                                   (self, file, file_offset))
        elif self['PosFormat'] == 2:
            self['ClassDef1'] = indirect(ClassDefinition)(self, file, file_offset)
            self['ClassDef2'] = indirect(ClassDefinition)(self, file, file_offset)
            self['Class1Count'] = uint16(file)
            self['Class2Count'] = uint16(file)


class PairSetTable(OpenTypeTable):
    entries = [('PairValueCount', uint16)]

    def __init__(self, file, file_offset, format_1, format_2):
        super().__init__(file, file_offset)
        pvr_reader = lambda file: PairValueRecord(file, format_1, format_2)
        self['PairValueRecord'] = array(pvr_reader, self['PairValueCount'])(file)


class PairValueRecord(OpenTypeTable):
    entries = [('SecondGlyph', glyph_id)]

    def __init__(self, file, format_1, format_2):
        super().__init__(file, None)
        self['Value1'] = ValueRecord(file, format_1)
        self['Value2'] = ValueRecord(file, format_2)


class ValueRecord(OpenTypeTable):
    formats = {'XPlacement': int16,
               'YPlacement': int16,
               'XAdvance': int16,
               'YAdvance': int16,
               'XPlaDevice': offset,
               'YPlaDevice': offset,
               'XAdvDevice': offset,
               'YAdvDevice': offset}

    def __init__(self, file, value_format):
        super().__init__(file, None)
        for name, present in value_format.items():
            if present:
                self[name] = self.formats[name](file)


class GposLookupTable(LookupTable):
    types = {2: PairAdjustmentSubtable}


class GposLookupListTable(OpenTypeTable):
    entries = [('LookupCount', uint16),
               ('Lookup', offset_array(GposLookupTable, 'LookupCount'))]
