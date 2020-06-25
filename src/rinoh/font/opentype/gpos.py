# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import struct

from .parse import OpenTypeTable, MultiFormatTable, Record
from .parse import int16, uint16, ushort, ulong, Packed
from .parse import array, context, context_array, indirect, indirect_array
from .layout import LayoutTable, Coverage, ClassDefinition, Device
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


class ValueRecord(OpenTypeTable):
    formats = {'XPlacement': int16,
               'YPlacement': int16,
               'XAdvance': int16,
               'YAdvance': int16,
               'XPlaDevice': indirect(Device),
               'YPlaDevice': indirect(Device),
               'XAdvDevice': indirect(Device),
               'YAdvDevice': indirect(Device)}

    def __init__(self, file, value_format):
        super().__init__(file)
        for name, present in value_format.items():
            if present:
                self[name] = self.formats[name](file)


class Anchor(MultiFormatTable):
    entries = [('AnchorFormat', uint16),
               ('XCoordinate', int16),
               ('YCoordinate', int16)]
    formats = {2: [('AnchorPoint', uint16)],
               3: [('XDeviceTable', indirect(Device)),
                   ('YDeviceTable', indirect(Device))]}


class MarkRecord(Record):
    entries = [('Class', uint16),
               ('MarkAnchor', indirect(Anchor))]


class MarkArray(OpenTypeTable):
    entries = [('MarkCount', uint16),
               ('MarkRecord', context_array(MarkRecord, 'MarkCount'))]


class SingleAdjustmentSubtable(MultiFormatTable):
    entries = [('PosFormat', uint16),
               ('Coverage', indirect(Coverage)),
               ('ValueFormat', ValueFormat)]
    formats = {1: [('ValueRecord', context(ValueRecord, 'ValueFormat'))],
               2: [('ValueCount', uint16),
                   ('ValueRecord', context_array(context(ValueRecord,
                                                         'ValueFormat'),
                                                 'ValueCount'))]}


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


class PairAdjustmentSubtable(MultiFormatTable):
    entries = [('PosFormat', uint16),
               ('Coverage', indirect(Coverage)),
               ('ValueFormat1', ValueFormat),
               ('ValueFormat2', ValueFormat)]
    formats = {1: [('PairSetCount', uint16),
                   ('PairSet', indirect_array(PairSetTable, 'PairSetCount',
                                              'ValueFormat1', 'ValueFormat2'))],
               2: [('ClassDef1', indirect(ClassDefinition)),
                   ('ClassDef2', indirect(ClassDefinition)),
                   ('Class1Count', uint16),
                   ('Class2Count', uint16)]}

    def __init__(self, file, file_offset=None):
        super().__init__(file, file_offset)
        format_1, format_2 = self['ValueFormat1'], self['ValueFormat2']
        if self['PosFormat'] == 2:
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


class EntryExitRecord(OpenTypeTable):
    entries = [('EntryAnchor', indirect(Anchor)),
               ('ExitAnchor', indirect(Anchor))]


class CursiveAttachmentSubtable(OpenTypeTable):
    entries = [('PosFormat', uint16),
               ('Coverage', indirect(Coverage)),
               ('EntryExitCount', uint16),
               ('EntryExitRecord', context_array(EntryExitRecord,
                                                 'EntryExitCount'))]

    def lookup(self, a_id, b_id):
        assert self['PosFormat'] == 1
        try:
            a_index = self['Coverage'].index(a_id)
            b_index = self['Coverage'].index(b_id)
        except ValueError:
            raise KeyError
        a_entry_exit = self['EntryExitRecord'][a_index]
        b_entry_exit = self['EntryExitRecord'][b_index]
        raise NotImplementedError


class MarkCoverage(OpenTypeTable):
    pass


class BaseCoverage(OpenTypeTable):
    pass


class Mark2Array(OpenTypeTable):
    pass


class BaseRecord(OpenTypeTable):
##    entries = [('BaseAnchor', indirect_array(Anchor, 'ClassCount'))]

    def __init__(self, file, file_offset, class_count):
        super().__init__(self, file, file_offset)
##        self['BaseAnchor'] = indirect_array(Anchor, 'ClassCount'])(file)


class BaseArray(OpenTypeTable):
    entries = [('BaseCount', uint16)]
##               ('BaseRecord', context_array(BaseRecord, 'BaseCount'))]

    def __init__(self, file, file_offset, class_count):
        super().__init__(self, file, file_offset)
        self['BaseRecord'] = array(BaseRecord, self['BaseCount'],
                                   class_count=class_count)(file)


class MarkToBaseAttachmentSubtable(OpenTypeTable):
    entries = [('PosFormat', uint16),
               ('MarkCoverage', indirect(MarkCoverage)),
               ('BaseCoverage', indirect(BaseCoverage)),
               ('ClassCount', uint16),
               ('MarkArray', indirect(MarkArray)),
               ('BaseArray', indirect(BaseArray, 'ClassCount'))]


class MarkToMarkAttachmentSubtable(OpenTypeTable):
    entries = [('PosFormat', uint16),
               ('Mark1Coverage', indirect(MarkCoverage)),
               ('Mark1Coverage', indirect(MarkCoverage)),
               ('ClassCount', uint16),
               ('Mark1Array', indirect(MarkArray)),
               ('Mark1Array', indirect(Mark2Array))]


class ExtensionPositioning(OpenTypeTable):
    entries = [('PosFormat', ushort),
               ('ExtensionLookupType', ushort),
               ('ExtensionOffset', ulong)]

    def __init__(self, file, file_offset=None):
        super().__init__(file, file_offset=file_offset)
        subtable_class = GposTable.lookup_types[self['ExtensionLookupType']]
        table_offset = file_offset + self['ExtensionOffset']
        self.subtable = subtable_class(file, table_offset)

    def lookup(self, *args, **kwargs):
        return self.subtable.lookup(*args, **kwargs)


class GposTable(LayoutTable):
    """Glyph positioning table"""
    tag = 'GPOS'
    lookup_types = {1: SingleAdjustmentSubtable,
                    2: PairAdjustmentSubtable,
                    3: CursiveAttachmentSubtable,
                    4: MarkToBaseAttachmentSubtable,
                    6: MarkToMarkAttachmentSubtable,
                    9: ExtensionPositioning}
