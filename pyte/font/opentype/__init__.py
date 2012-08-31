
import ctypes

from .. import Font
from ..style import MEDIUM, UPRIGHT, NORMAL, ITALIC
from ..metrics import FontMetrics, GlyphMetrics

from .parse import OpenTypeParser, NAME_PS_NAME


class OpenTypeFont(Font, dict):
    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.encoding = None
        super().__init__(weight, slant, width)
        self.tables = OpenTypeParser(filename)
        self.metrics = OpenTypeMetrics(self.tables)

    @property
    def name(self):
        return self.metrics.name

    def get_glyph(self, char, variant=None):
        return self.metrics._glyphs[char]

    def get_ligature(self, glyph, successor_glyph):
        return None

    def get_kerning(self, a, b):
        return 0.0


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
            width = tables['hmtx']['hMetrics'][glyph_index]
            self._glyphs[chr(ordinal)] = GlyphMetrics(None, width,
                                                      None, glyph_index)

    @property
    def name(self):
        return self._tables.name[NAME_PS_NAME]
