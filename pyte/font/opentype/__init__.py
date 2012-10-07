
import ctypes

from warnings import warn

from .. import Font
from ..style import MEDIUM, UPRIGHT, NORMAL, ITALIC
from ..metrics import FontMetrics, GlyphMetrics
from ...warnings import PyteWarning

from .parse import OpenTypeParser, NAME_PS_NAME


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
        self._suffixes = {}
        self._ligatures = {}
        self._kerning_pairs = {}
        # TODO: differentiate between TT/CFF
        # TODO: extract bboxes: http://www.tug.org/TUGboat/tb24-3/bella.pdf
        for ordinal, glyph_index in tables['cmap'][(3, 1)].items():
            width = tables['hmtx']['advanceWidth'][glyph_index]
            self._glyphs[chr(ordinal)] = GlyphMetrics(None, width,
                                                      None, glyph_index)

        self.bbox = tables['CFF'].top_dicts[0]['FontBBox']
        self.italic_angle = tables['post']['italicAngle']
        self.ascent = tables['hhea']['Ascender']
        self.descent = tables['hhea']['Descender']
        self.cap_height = tables['OS/2']['sCapHeight']
        self.x_height = tables['OS/2']['sxHeight']
        self.stem_v = 50 # self['FontMetrics']['StdVW']

    @property
    def name(self):
        return self._tables['name'][NAME_PS_NAME]

    def get_glyph(self, char, variant=None):
        try:
            return self._glyphs[char]
        except KeyError:
            warn('{} does not contain glyph for unicode index 0x{:04x} ({})'
                 .format(self.name, ord(char), char), PyteWarning)
            return self._glyphs['?']

    def get_ligature(self, glyph, successor_glyph):
        return None

    def get_kerning(self, a, b):
        return 0.0
