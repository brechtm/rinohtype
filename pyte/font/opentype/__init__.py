
import ctypes

from .. import Font
from ..style import MEDIUM, UPRIGHT, NORMAL, ITALIC
from ..metrics import FontMetrics, GlyphMetrics

from .parse import OpenTypeParser, NAME_PS_NAME


class OpenTypeFont(Font, dict):
    def __init__(self, filename, weight=MEDIUM, slant=UPRIGHT, width=NORMAL):
        self.metrics = None
        self.encoding = None
        super().__init__(weight, slant, width)
        self.tables = OpenTypeParser(filename)
        # TODO: extract data from tables
##        self.metrics = FontMetrics()
##        for glyph in ...:
##            glyph_metrics = GlyphMetrics(None?, width, bounding_box, code)
##            self.metrics.glyphs[glyph_metrics.code] = glyph_metrics
        # TODO: self.metrics.kerning_pairs
        # TODO: self.metrics.ligatures

    @property
    def name(self):
        return self.tables.name[NAME_PS_NAME]


class OpenTypeMetrics(FontMetrics):
    def __init__(self, opentype_font):
        super().__init__()
        self._font = opentype_font
        self._glyphs = {}
        self._suffixes = {}
        self._ligatures = {}
        self._kerning_pairs = {}

    @property
    def name(self):
        return self._font.name



##class CMapTable(object):
##    def __init__(self):
##        pass
##
##    def __getitem__(self, index):
##        raise NotImplementedError
##
##
##class CMapTable4(CMapTable):
##    def __init__(self):
##        pass
##
##    def __getitem__(self, index):
##        raise NotImplementedError
