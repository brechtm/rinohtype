
from .parse import OpenTypeTable, MultiFormatTable
from .parse import fixed, int16, uint16, tag, glyph_id, offset, array, indirect
from .parse import context_array, indirect_array, Packed
from .layout import LayoutTable, ScriptListTable, FeatureListTable, LookupTable
from .layout import Coverage, ClassDefinition


# Single subsitution (subtable format 1)
class SingleSubTable(MultiFormatTable):
    entries = [('SubstFormat', uint16),
               ('Coverage', indirect(Coverage))]
    formats = {1: [('DeltaGlyphID', glyph_id)],
               2: [('GlyphCount', uint16),
                   ('Substitute', context_array(glyph_id, 'GlyphCount'))]}

    def lookup(self, glyph_id):
        try:
            index = self['Coverage'].index(glyph_id)
        except ValueError:
            raise KeyError
        if self['SubstFormat'] == 1:
            return index + self['DeltaGlyphID']
        else:
            return self['Substitute'][index]


# Alternate subtitition (subtable format 3)
class AlternateSubTable(OpenTypeTable):
    pass


# Ligature subsitution (subtable format 4)
class Ligature(OpenTypeTable):
    entries = [('LigGlyph', glyph_id),
               ('CompCount', uint16)]

    def __init__(self, file, file_offset):
        super().__init__(file, file_offset)
        self['Component'] = array(glyph_id, self['CompCount'] - 1)(file)


class LigatureSet(OpenTypeTable):
    entries = [('LigatureCount', uint16),
               ('Ligature', indirect_array(Ligature, 'LigatureCount'))]


class LigatureSubTable(OpenTypeTable):
    entries = [('SubstFormat', uint16),
               ('Coverage', indirect(Coverage)),
               ('LigSetCount', uint16),
               ('LigatureSet', indirect_array(LigatureSet, 'LigSetCount'))]

    def lookup(self, a_id, b_id):
        try:
            index = self['Coverage'].index(a_id)
        except ValueError:
            raise KeyError
        ligature_set = self['LigatureSet'][index]
        for ligature in ligature_set['Ligature']:
            if ligature['Component'] == [b_id]:
                return ligature['LigGlyph']
        raise KeyError


# Chaining contextual subsitution (subtable format 6)
class ChainSubRule(OpenTypeTable):
    pass
##    entries = [('BacktrackGlyphCount', uint16),
##               ('Backtrack', context_array(glyph_id, 'BacktrackGlyphCount')),
##               ('InputGlyphCount', uint16),
##               ('Input', context_array(glyph_id, 'InputGlyphCount',
##                                       lambda count: count - 1)),
##               ('LookaheadGlyphCount', uint16),
##               ('LookAhead', context_array(glyph_id, 'LookaheadGlyphCount')),
##               ('SubstCount', uint16),
##               ('SubstLookupRecord', context_array(glyph_id, 'SubstCount'))]


class ChainSubRuleSet(OpenTypeTable):
    entries = [('ChainSubRuleCount', uint16),
               ('ChainSubRule', indirect(ChainSubRule))]


class ChainingContextSubtable(MultiFormatTable):
    entries = [('SubstFormat', uint16)]
    formats = {1: [('Coverage', indirect(Coverage)),
                   ('ChainSubRuleSetCount', uint16),
                   ('ChainSubRuleSet', indirect_array(ChainSubRuleSet,
                                                      'ChainSubRuleSetCount'))]}


class GsubTable(LayoutTable):
    """Glyph substitution table"""
    tag = 'GSUB'
    lookup_types = {1: SingleSubTable,
                    3: AlternateSubTable,
                    4: LigatureSubTable}#,
                    #6: ChainingContextSubtable}
