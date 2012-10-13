
import struct

from .parse import OpenTypeTable, MultiFormatTable, context_array, indirect_array
from .parse import fixed, int16, uint16, tag, glyph_id, offset, array, indirect
from .parse import Packed
from .layout import LayoutTable, ScriptListTable, FeatureListTable, LookupTable
from .layout import Coverage, ClassDefinition
from ...util import cached_property


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
    def present_keys(self):
        keys = []
        for name, present in self.items():
            if present:
                keys.append(name)
        return keys


class SingleAdjustmentSubtable(OpenTypeTable):
    pass


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

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        format_1, format_2 = self['ValueFormat1'], self['ValueFormat2']
        if self['PosFormat'] == 1:
            pst_reader = (lambda file, file_offset: PairSetTable(file,
                                                                 file_offset,
                                                                 format_1,
                                                                 format_2))
            self['PairSet'] = (indirect_array(pst_reader, 'PairSetCount')
                                   (self, file, file_offset))
        elif self['PosFormat'] == 2:
            record_format = format_1.data_format + format_2.data_format
            c2r_struct = struct.Struct('>' + record_format)
            c2r_size = c2r_struct.size
            value_1_length = len(format_1)
            format_1_keys = format_1.present_keys
            format_2_keys = format_2.present_keys
            class_1_record = []
            for i in range(self['Class1Count']):
                class_2_record = []
                for j in range(self['Class2Count']):
                    record_data = c2r_struct.unpack(file.read(c2r_size))
                    value_1 = {}
                    value_2 = {}
                    for i, key in enumerate(format_1_keys):
                        value_1[key] = record_data[i]
                    for i, key in enumerate(format_2_keys):
                        value_2[key] = record_data[value_1_length + i]
                    class_2_record.append({'Value1': value_1,
                                           'Value2': value_2})
                class_1_record.append(class_2_record)
            self['Class1Record'] = class_1_record

    def lookup(self, a_id, b_id):
        if self['PosFormat'] == 1:
            try:
                index = self['Coverage'].index(a_id)
            except ValueError:
                raise KeyError
            pair_value_record = self['PairSet'][index].by_second_glyph_id[b_id]
            return pair_value_record['Value1']['XAdvance']
        elif self['PosFormat'] == 2:
            a_class = self['ClassDef1'].class_number(a_id)
            b_class = self['ClassDef2'].class_number(b_id)
            class_2_record = self['Class1Record'][a_class][b_class]
            return class_2_record['Value1']['XAdvance']


class PairSetTable(OpenTypeTable):
    entries = [('PairValueCount', uint16)]

    def __init__(self, file, file_offset, format_1, format_2):
        super().__init__(file, file_offset)
        record_format = format_1.data_format + format_2.data_format
        value_1_length = len(format_1)
        format_1_keys = format_1.present_keys
        format_2_keys = format_2.present_keys
        pvr_struct = struct.Struct('>H' + record_format)
        pvr_size = pvr_struct.size
        pvr_list = []
        self.by_second_glyph_id = {}
        for i in range(self['PairValueCount']):
            record_data = pvr_struct.unpack(file.read(pvr_size))
            second_glyph = record_data[0]
            value_1 = {}
            value_2 = {}
            for i, key in enumerate(format_1_keys):
                value_1[key] = record_data[1 + i]
            for i, key in enumerate(format_2_keys):
                value_2[key] = record_data[1 + value_1_length + i]
            pvr = {'Value1': value_1,
                   'Value2': value_2}
            pvr_list.append(pvr)
            self.by_second_glyph_id[second_glyph] = pvr
        self['PairValueRecord'] = pvr_list


class GposTable(LayoutTable):
    """Glyph positioning table"""
    tag = 'GPOS'
    lookup_types = {1: SingleAdjustmentSubtable,
                    2: PairAdjustmentSubtable}
