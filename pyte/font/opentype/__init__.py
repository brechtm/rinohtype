
import ctypes

from warnings import warn

from ...warnings import PyteWarning
from .. import Font
from ..metrics import FontMetrics, GlyphMetrics
from ..style import MEDIUM, UPRIGHT, NORMAL, ITALIC
from ..style import SMALL_CAPITAL

from .parse import OpenTypeParser
from .ids import NAME_PS_NAME, PLATFORM_WINDOWS, LANGUAGE_WINDOWS_EN_US


class OpenTypeFont(Font):
    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.filename = filename
        self.encoding = None
        super().__init__(weight, slant, width)
        self.tables = OpenTypeParser(filename)
        self.metrics = OpenTypeMetrics(self.tables)

    @property
    def name(self):
        return self.metrics.name


class OpenTypeMetrics(FontMetrics):
    def __init__(self, tables):
        super().__init__()
        self._tables = tables
        self._glyphs = {}
        self._glyphs_by_code = {}
        self._suffixes = {}
        self._ligatures = {}
        self._kerning_pairs = {}
        # TODO: differentiate between TT/CFF
        # TODO: extract bboxes: http://www.tug.org/TUGboat/tb24-3/bella.pdf
        for glyph_index, width in enumerate(tables['hmtx']['advanceWidth']):
            glyph_metrics = GlyphMetrics(None, width, None, glyph_index)
            self._glyphs_by_code[glyph_index] = glyph_metrics
        for encoding in [(1, 0), (3, 1)]:
            if encoding not in tables['cmap']:
                continue
            for ordinal, glyph_index in tables['cmap'][encoding].items():
                self._glyphs[chr(ordinal)] = self._glyphs_by_code[glyph_index]
        assert self._glyphs
        self.bbox = tables['head'].bounding_box
        self.italic_angle = tables['post']['italicAngle']
        self.ascent = tables['hhea']['Ascender']
        self.descent = tables['hhea']['Descender']
        self.cap_height = tables['OS/2']['sCapHeight']
        self.x_height = tables['OS/2']['sxHeight']
        self.stem_v = 50 # self['FontMetrics']['StdVW']

    @property
    def name(self):
        names = self._tables['name'].strings
        return names[NAME_PS_NAME][PLATFORM_WINDOWS][LANGUAGE_WINDOWS_EN_US]

    def get_glyph(self, char, variant=None):
        try:
            glyph = self._glyphs[char]
        except KeyError:
            warn('{} does not contain glyph for unicode index 0x{:04x} ({})'
                 .format(self.name, ord(char), char), PyteWarning)
            return self._glyphs['?']
        if variant == SMALL_CAPITAL:
            lookup_tables = self._get_lookup_tables('GSUB', 'smcp', 'latn')
            for lookup_table in lookup_tables:
                try:
                    code = lookup_table.lookup(glyph.code)
                    return self._glyphs_by_code[code]
                except KeyError:
                    pass
        return glyph

    def _get_lookup_tables(self, table, feature, script='DFLT', language=None):
        lookup_tables = self._tables[table]['LookupList']['Lookup']
        try:
            script_table = self._tables[table]['ScriptList'].by_tag[script][0]
        except KeyError:
            if script != 'DFLT':
                warn('{} does not support the script "{}". Trying default '
                     'script.'.format(self.name, script, PyteWarning))
                return self._get_lookup_tables(table, feature)
            else:
                warn('{} has no default script defined.'
                     .format(self.name, PyteWarning))
                raise
        if language:
            try:
                lang_sys_table = script_table.by_tag[language][0]
            except KeyError:
                warn('{} does not support the language "{}". Falling back to '
                     'defaults.'.format(self.name, language, PyteWarning))
            lang_sys_table = script_table['DefaultLangSys']
        else:
            lang_sys_table = script_table['DefaultLangSys']
        feature_indices = lang_sys_table['FeatureIndex']
        for index in feature_indices:
            record = self._tables[table]['FeatureList']['Record'][index]
            if record['Tag'] == feature:
                lookup_list_indices = record['Value']['LookupListIndex']
                return [lookup_tables[lookup_list_index]
                        for lookup_list_index in lookup_list_indices]

    def get_ligature(self, glyph, successor_glyph):
        lookup_tables = self._get_lookup_tables('GSUB', 'liga', 'latn')
        for lookup_table in lookup_tables:
            try:
                code = lookup_table.lookup(glyph.code, successor_glyph.code)
                return self._glyphs_by_code[code]
            except KeyError:
                pass
        return None

    def get_kerning(self, a, b):
        lookup_tables = self._get_lookup_tables('GPOS', 'kern', 'latn')
        # TODO: 'kern' lookup list indices can point to pair adjustment (2) or
        #       Chained Context positioning (8) lookup subtables
        for lookup_table in lookup_tables:
            try:
                return lookup_table.lookup(a.code, b.code)
            except KeyError:
                pass
        return 0.0
