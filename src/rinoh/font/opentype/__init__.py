# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from logging import warning
from warnings import warn

from ...font.style import FontVariant, FontWeight, FontSlant, FontWidth
from ...util import cached
from ...warnings import RinohWarning
from .. import Font, GlyphMetrics, LeafGetter, MissingGlyphException

from .parse import OpenTypeParser
from .ids import NAME_PS_NAME, PLATFORM_WINDOWS, LANGUAGE_WINDOWS_EN_US


class OpenTypeFont(Font, OpenTypeParser):
    units_per_em = LeafGetter('head', 'unitsPerEm')
    encoding = None

    @property
    def name(self):
        names = self['name'].strings
        return names[NAME_PS_NAME][PLATFORM_WINDOWS][LANGUAGE_WINDOWS_EN_US]

    @property
    def bounding_box(self):
        return self['head'].bounding_box

    fixed_pitch = LeafGetter('post', 'isFixedPitch')
    italic_angle = LeafGetter('post', 'italicAngle')
    ascender = LeafGetter('OS/2', 'sTypoAscender')
    descender = LeafGetter('OS/2', 'sTypoDescender')
    line_gap = LeafGetter('OS/2', 'sTypoLineGap')
    cap_height = LeafGetter('OS/2', 'sCapHeight')
    x_height = LeafGetter('OS/2', 'sxHeight')
    stem_v = 50

    def __init__(self, filename, weight=None, slant=None, width=None):
        OpenTypeParser.__init__(self, filename)
        slant_ = (self['OS/2'].oblique and FontSlant.OBLIQUE
                  or self['OS/2'].italic and FontSlant.ITALIC
                  or FontSlant.UPRIGHT)
        weight = self._check('weight', weight, self['OS/2']['usWeightClass'],
                             FontWeight.to_name)
        slant = self._check('slant', slant, slant_)
        width = self._check('width', width, self['OS/2']['usWidthClass'],
                            FontWidth.to_name)
        super().__init__(filename, weight, slant, width)
        self._glyphs_by_code = self._create_glyph_metrics()
        self._glyphs = self._create_glyphs_by_char(self._glyphs_by_code)
        self._suffixes = {}
        self._ligatures = {}
        self._kerning_pairs = {}

    def _check(self, attr, specified, determined, convert=lambda value: value):
        if specified and specified != determined:
            warning("{name}: specified font {attr} '{spec}' does not "
                    "match the {attr} reported by the font file ({rep})"
                    .format(name=self.name, attr=attr, spec=convert(specified),
                            rep=convert(determined)))
            return specified
        return determined

    def _create_glyph_metrics(self):
        glyphs_by_code = {}
        # TODO: extract bboxes from CFF: www.tug.org/TUGboat/tb24-3/bella.pdf
        advance_width_table = self['hmtx']['advanceWidth']
        glyf_table = self['glyf'] if 'glyf' in self else None
        for glyph_index, width in enumerate(advance_width_table):
            bbox = (glyf_table[glyph_index].bounding_box
                    if glyf_table and glyph_index in glyf_table
                    else None)
            glyph_metrics = GlyphMetrics(None, width, bbox, glyph_index)
            glyphs_by_code[glyph_index] = glyph_metrics
        return glyphs_by_code

    def _create_glyphs_by_char(self, glyphs_by_code):
        # TODO: support symbol/wingdings
        #       "The 'cmap' subtable (platform 3, encoding 0) must use format 4.
        #       The character codes should start at 0xF000, which is in the
        #       Private Use Area of Unicode. It is suggested to derive the
        #       format 4 encodings by simply adding 0xF000 to the format 0
        #       (Macintosh) encodings."
        # TODO: properly handle encodings
        glyphs_by_char = {}
        cmap_tables = self['cmap']
        for encoding in [(0, 0), (0, 1), (0, 2), (0, 3), (3, 1)]:
            try:
                for ordinal, index in cmap_tables[encoding].mapping.items():
                    glyphs_by_char[chr(ordinal)] = glyphs_by_code[index]
                break
            except KeyError:
                continue
        if not glyphs_by_char:
            raise Exception
        return glyphs_by_char

    _VARIANTS = {FontVariant.SMALL_CAPITAL: 'smcp',
                 FontVariant.OLDSTYLE_FIGURES: 'onum'}

    def get_glyph(self, char, variant):
        try:
            glyph = self._glyphs[char]
        except KeyError:
            warn('{} does not contain glyph for unicode index 0x{:04x} ({})'
                 .format(self.name, ord(char), char), RinohWarning)
            raise MissingGlyphException(char)

        if variant in self._VARIANTS and 'GSUB' in self:
            feature = self._VARIANTS[variant]
            lookup_tables = self._get_lookup_tables('GSUB', feature, 'latn')
            for lookup_table in lookup_tables:
                try:
                    code = lookup_table.lookup(glyph.code)
                    return self._glyphs_by_code[code]
                except KeyError:
                    pass
        return glyph

    def _get_lookup_tables(self, table, feature, script='DFLT', language=None):
        lookup_tables = self[table]['LookupList']['Lookup']
        try:
            script_table = self[table]['ScriptList'].by_tag[script][0]
        except KeyError:
            if script != 'DFLT':
                warn('{} does not support the script "{}". Trying default '
                     'script.'.format(self.name, script, RinohWarning))
                try:
                    return self._get_lookup_tables(table, feature)
                except KeyError:
                    return []
            else:
                warn('{} has no default script defined.'
                     .format(self.name, RinohWarning))
                raise
        if language:
            try:
                lang_sys_table = script_table.by_tag[language][0]
            except KeyError:
                warn('{} does not support the language "{}". Falling back to '
                     'defaults.'.format(self.name, language, RinohWarning))
                lang_sys_table = script_table['DefaultLangSys']
        else:
            lang_sys_table = script_table['DefaultLangSys']
        feature_indices = lang_sys_table['FeatureIndex']
        for index in feature_indices:
            record = self[table]['FeatureList']['Record'][index]
            if record['Tag'] == feature:
                lookup_list_indices = record['Value']['LookupListIndex']
                return [lookup_tables[lookup_list_index]
                        for lookup_list_index in lookup_list_indices]
        return []

    @cached
    def get_ligature(self, glyph, successor_glyph):
        if 'GSUB' in self:
            lookup_tables = self._get_lookup_tables('GSUB', 'liga', 'latn')
            for lookup_table in lookup_tables:
                try:
                    code = lookup_table.lookup(glyph.code, successor_glyph.code)
                    return self._glyphs_by_code[code]
                except KeyError:
                    pass
        return None

    @cached
    def get_kerning(self, a, b):
        if 'GPOS' in self:
            lookup_tables = self._get_lookup_tables('GPOS', 'kern', 'latn')
            # TODO: 'kern' lookup list indices can point to pair adjustment (2)
            #       or Chained Context positioning (8) lookup subtables
            for lookup_table in lookup_tables:
                try:
                    return lookup_table.lookup(a.code, b.code)
                except KeyError:
                    pass
        if 'kern' in self:
            try:
                return self['kern'][0].pairs[a.code][b.code]
            except KeyError:
                pass
        return 0.0
