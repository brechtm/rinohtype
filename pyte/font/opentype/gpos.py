
import struct

from .tables import OpenTypeTable, MultiFormatTable, context_array, offset_array
from .parse import fixed, int16, uint16, tag, glyph_id, offset, array, indirect
from .parse import Packed
from .layout import LayoutTable, ScriptListTable, FeatureListTable, LookupTable
from .layout import Coverage, ClassDefinition
from ...util import timed, cached_property

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
    formats = {'XPlacement': 'h',
               'YPlacement': 'h',
               'XAdvance': 'h',
               'YAdvance': 'h',
               'XPlaDevice': 'H',
               'YPlaDevice': 'H',
               'XAdvDevice': 'H',
               'YAdvDevice': 'H'}

    @cached_property
    def data_format(self):
        data_format = ''
        for name, present in self.items():
            if present:
                data_format += self.formats[name]
        return data_format

    @cached_property
    def value_record_type(self):
        formats = {'XPlacement': int16,
                   'YPlacement': int16,
                   'XAdvance': int16,
                   'YAdvance': int16,
                   'XPlaDevice': offset,
                   'YPlaDevice': offset,
                   'XAdvDevice': offset,
                   'YAdvDevice': offset}
        entries = []
        for name, present in self.items():
            if present:
                entries.append((name, formats[name]))

        class ValueRecord(OpenTypeTable):
            entries = entries
            num_entries = len(entries)

            def __init__(self, file, value_format):
                super().__init__(file, None)
                for name, present in value_format.items():
                    if present:
                        self[name] = self.formats[name](file)
        return ValueRecord


class SingleAdjustmentSubtable(OpenTypeTable):
    pass


class Class2Record(OpenTypeTable):
    def __init__(self, file, record_struct, value_1_length):
        super().__init__(file)
##        self['Value1'] = ValueRecord(file, format_1)
##        self['Value2'] = ValueRecord(file, format_2)
        data = record_struct.unpack(file.read(record_struct.size))
        data_1, data_2 = data[:value_1_length], data[value_1_length:]
        self['Value1'] = data_1
        self['Value2'] = data_2


# TODO: MultiFormatTable
class PairAdjustmentSubtable(MultiFormatTable):
    entries = [('PosFormat', uint16),
               ('Coverage', indirect(Coverage)),
               ('ValueFormat1', ValueFormat),
               ('ValueFormat2', ValueFormat)]
    formats = {1: [('PairSetCount', uint16)],
               2: [('ClassDef1', indirect(ClassDefinition)),
                   ('ClassDef2', indirect(ClassDefinition)),
                   ('Class1Count', uint16),
                   ('Class2Count', uint16)]}

    @timed
    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        format_1, format_2 = self['ValueFormat1'], self['ValueFormat2']
        if self['PosFormat'] == 1:
            record_format = format_1.data_format + format_2.data_format
            value_1_length = len(format_1)
            pst_reader = (lambda file, file_offset: PairSetTable(file,
                                                                 file_offset,
                                                                 record_format,
                                                                 value_1_length))
            self['PairSet'] = (offset_array(pst_reader, 'PairSetCount')
                                   (self, file, file_offset))
        elif self['PosFormat'] == 2:
            self['Class1Record'] = [[Class2Record(file, format_1, format_2)
                                     for j in range(self['Class2Count'])]
                                    for i in range(self['Class1Count'])]

    def lookup(self, a_id, b_id):
        if self['PosFormat'] == 1:
            try:
                index = self['Coverage'].index(a_id)
            except ValueError:
                raise KeyError
            pair_value_record = self['PairSet'][index].by_second_glyph_id[b_id]
##            return pair_value_record['Value1']['XAdvance']
            return pair_value_record['Value1'][0]
        elif self['PosFormat'] == 2:
            a_class = self['ClassDef1'].class_number(a_id)
            b_class = self['ClassDef2'].class_number(b_id)
            class_2_record = self['Class1Record'][a_class][b_class]
            return class_2_record['Value1']['XAdvance']


class PairSetTable(OpenTypeTable):
    entries = [('PairValueCount', uint16)]

    def __init__(self, file, file_offset, record_format, value_1_length):
        super().__init__(file, file_offset)
        pvr_struct = struct.Struct('>H' + record_format)
        pvr_size = pvr_struct.size
        pvr_list = []
        self.by_second_glyph_id = {}
        for i in range(self['PairValueCount']):
            record_bytes = file.read(pvr_size)
            record_data = pvr_struct.unpack(record_bytes)
            second_glyph = record_data[0]
            pvr = {'Value1': record_data[1:value_1_length + 1],
                   'Value2': record_data[value_1_length + 1:]}
            pvr_list.append(pvr)
            self.by_second_glyph_id[second_glyph] = pvr
        self['PairValueRecord'] = pvr_list


##class ValueRecord(OpenTypeTable):
##    formats = {'XPlacement': int16,
##               'YPlacement': int16,
##               'XAdvance': int16,
##               'YAdvance': int16,
##               'XPlaDevice': offset,
##               'YPlaDevice': offset,
##               'XAdvDevice': offset,
##               'YAdvDevice': offset}
##
##    def __init__(self, file, value_format):
##        super().__init__(file, None)
##        for name, present in value_format.items():
##            if present:
##                self[name] = self.formats[name](file)


class GposTable(LayoutTable):
    """Glyph positioning table"""
    tag = 'GPOS'
    lookup_types = {1: SingleAdjustmentSubtable,
                    2: PairAdjustmentSubtable}
