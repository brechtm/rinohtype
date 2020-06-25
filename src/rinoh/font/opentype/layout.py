# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .parse import OpenTypeTable, MultiFormatTable, Record, context_array
from .parse import fixed, array, uint16, tag, glyph_id, offset, indirect, Packed


class ListRecord(Record):
    entries = [('Tag', tag),
               ('Offset', offset)]

    def parse_value(self, file, file_offset, entry_type):
        self['Value'] = entry_type(file, file_offset + self['Offset'])


class ListTable(OpenTypeTable):
    entry_type = None
    entries = [('Count', uint16),
               ('Record', context_array(ListRecord, 'Count'))]

    def __init__(self, file, file_offset, **kwargs):
        super().__init__(file, file_offset)
        self.by_tag = {}
        for record in self['Record']:
            record.parse_value(file, file_offset, self.entry_type)
            tag_list = self.by_tag.setdefault(record['Tag'], [])
            tag_list.append(record['Value'])


class LangSysTable(OpenTypeTable):
    entries = [('LookupOrder', offset),
               ('ReqFeatureIndex', uint16),
               ('FeatureCount', uint16),
               ('FeatureIndex', context_array(uint16, 'FeatureCount'))]


class ScriptTable(ListTable):
    entry_type = LangSysTable
    entries = [('DefaultLangSys', indirect(LangSysTable))] + ListTable.entries


class ScriptListTable(ListTable):
    entry_type = ScriptTable


class FeatureTable(OpenTypeTable):
    entries = [('FeatureParams', offset),
               ('LookupCount', uint16),
               ('LookupListIndex', context_array(uint16, 'LookupCount'))]

    def __init__(self, file, offset):
        super().__init__(file, offset)
        if self['FeatureParams']:
            # TODO: parse Feature Parameters
            pass
        else:
            del self['FeatureParams']


class FeatureListTable(ListTable):
    entry_type = FeatureTable


class LookupFlag(Packed):
    reader = uint16
    fields = [('RightToLeft', 0x0001, bool),
              ('IgnoreBaseGlyphs', 0x0002, bool),
              ('IgnoreLigatures', 0x0004, bool),
              ('IgnoreMarks', 0x0008, bool),
              ('UseMarkFilteringSet', 0x010, bool),
              ('MarkAttachmentType', 0xFF00, int)]


class RangeRecord(OpenTypeTable):
    entries = [('Start', glyph_id),
               ('End', glyph_id),
               ('StartCoverageIndex', uint16)]


class Coverage(MultiFormatTable):
    entries = [('CoverageFormat', uint16)]
    formats = {1: [('GlyphCount', uint16),
                   ('GlyphArray', context_array(glyph_id, 'GlyphCount'))],
               2: [('RangeCount', uint16),
                   ('RangeRecord', context_array(RangeRecord, 'RangeCount'))]}

    def index(self, glyph_id):
        if self['CoverageFormat'] == 1:
            return self['GlyphArray'].index(glyph_id)
        else:
            for record in self['RangeRecord']:
                if record['Start'] <= glyph_id <= record['End']:
                    return (record['StartCoverageIndex']
                            + glyph_id - record['Start'])
            raise ValueError


class ClassRangeRecord(OpenTypeTable):
    entries = [('Start', glyph_id),
               ('End', glyph_id),
               ('Class', uint16)]


class ClassDefinition(MultiFormatTable):
    entries = [('ClassFormat', uint16)]
    formats = {1: [('StartGlyph', glyph_id),
                   ('GlyphCount', uint16),
                   ('ClassValueArray', context_array(uint16, 'GlyphCount'))],
               2: [('ClassRangeCount', uint16),
                   ('ClassRangeRecord', context_array(ClassRangeRecord,
                                                      'ClassRangeCount'))]}

    def class_number(self, glyph_id):
        if self['ClassFormat'] == 1:
            index = glyph_id - self['StartGlyph']
            if 0 <= index < self['GlyphCount']:
                return self['ClassValueArray'][index]
        else:
            for record in self['ClassRangeRecord']:
                if record['Start'] <= glyph_id <= record['End']:
                    return record['Class']
        return 0


def subtables(subtable_type, file, file_offset, offsets):
    """Skip lookup types/subtables that are not yet implemented"""
    for subtable_offset in offsets:
        try:
            yield subtable_type(file, file_offset + subtable_offset)
        except KeyError:
            continue


class LookupTable(OpenTypeTable):
    entries = [('LookupType', uint16),
               ('LookupFlag', LookupFlag),
               ('SubTableCount', uint16)]

    def __init__(self, file, file_offset, subtable_types):
        super().__init__(file, file_offset)
        offsets = array(uint16, self['SubTableCount'])(file)
        if self['LookupFlag']['UseMarkFilteringSet']:
            self['MarkFilteringSet'] = uint16(file)
        subtable_type = subtable_types[self['LookupType']]
        self['SubTable'] = list(subtables(subtable_type, file, file_offset,
                                          offsets))

    def lookup(self, *args, **kwargs):
        for subtable in self['SubTable']:
            try:
                return subtable.lookup(*args, **kwargs)
            except KeyError:
                pass
        raise KeyError


class DelayedList(list):
    def __init__(self, reader, file, file_offset, item_offsets):
        super().__init__([None] * len(item_offsets))
        self._reader = reader
        self._file = file
        self._offsets = [file_offset + item_offset
                         for item_offset in item_offsets]

    def __getitem__(self, index):
        if super().__getitem__(index) is None:
            self[index] = self._reader(self._file, self._offsets[index])
        return super().__getitem__(index)


class LookupListTable(OpenTypeTable):
    entries = [('LookupCount', uint16)]

    def __init__(self, file, file_offset, types):
        super().__init__(file, file_offset)
        lookup_offsets = array(offset, self['LookupCount'])(file)
        lookup_reader = lambda file, file_offset: LookupTable(file, file_offset,
                                                              types)
        self['Lookup'] = DelayedList(lookup_reader, file, file_offset,
                                     lookup_offsets)


class LayoutTable(OpenTypeTable):
    entries = [('Version', fixed),
               ('ScriptList', indirect(ScriptListTable)),
               ('FeatureList', indirect(FeatureListTable))]

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        lookup_list_offset = offset(file)
        self['LookupList'] = LookupListTable(file,
                                             file_offset + lookup_list_offset,
                                             self.lookup_types)


class Device(OpenTypeTable):
    entries = [('StartSize', uint16),
               ('EndSize', uint16),
               ('DeltaFormat', uint16),
               ('DeltaValue', uint16)]
