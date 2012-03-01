
import os
import unicodedata
from warnings import warn

from psg.fonts.afm_metrics import afm_metrics

from .unit import pt
from .font import TypeFamily
from .text import ParentStyle, Style, CharacterLike, Box, NewLine, Tab
from .text import MixedStyledText
from .paragraph import Paragraph, ParagraphStyle, TabStop, RIGHT, CENTER
from .mathtext import Fonts, MathtextBackendPs, MathTextWarning, Parser, Bunch
from .mathtext import get_unicode_index
from ._mathtext_data import tex2uni


class MathFonts(object):
    default = None

    def __init__(self, roman, italic, bold, sans, mono, cal, symbol, fallback):
        self.roman = roman
        self.italic = italic
        self.bold = bold
        self.sans = sans
        self.mono = mono
        self.cal = cal
        self.symbol = symbol
        self.fallback = fallback


class MathStyle(Style):
    attributes = {'fonts': None, # no default fonts yet
                  'fontSize': 10*pt}

    def __init__(self, name, base=ParentStyle, **attributes):
        super().__init__(name, base=base, **attributes)


class Math(CharacterLike):
    style_class = MathStyle
    _parser = None

    def __init__(self, equation, style=ParentStyle):
        super().__init__(style)
        self.equation = equation

    def characters(self):
        font_output = PyteFonts(self)
        fontsize = float(self.get_style('fontSize'))
        dpi = 72

        # This is a class variable so we don't rebuild the parser
        # with each request.
        if self._parser is None:
            self.__class__._parser = Parser()

        s = '${}$'.format(self.equation)
        box = self._parser.parse(s, font_output, fontsize, dpi)
        font_output.set_canvas_size(box.width, box.height, box.depth)
        (width, height_depth, depth,
         pswriter, used_characters) = font_output.get_results(box)

        box = Box(width, height_depth - depth, depth, pswriter.getvalue())
        box.parent = self
        return [box]


 # TODO: is subclass of ParagraphStyle, but doesn't need all of its attributes!
class EquationStyle(ParagraphStyle):
    attributes = {'math_style': None,
                  'tab_stops': [TabStop(0.5, CENTER), TabStop(1.0, RIGHT)]}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Equation(Paragraph):
    style_class = EquationStyle
    next_number = 1

    def __init__(self, equation, style=None):
        self.ref = str(self.next_number)
        number = '({})'.format(self.next_number)
        self.__class__.next_number += 1
        math = Math(equation, style=style.math_style)
        math.parent = self # TODO: encapsulate
        text = [Tab(), math, Tab(), number]
        super().__init__(text, style)

    def reference(self):
        return self.ref


# adapted from matplotlib.mathtext.StandardPsFonts
class PyteFonts(Fonts):
    def __init__(self, styled):
        Fonts.__init__(self, None, MathtextBackendPs())
        self.styled = styled
        self.glyphd = {}
        self.fonts = {}

        type_family = self.styled.get_style('fonts')
        self.fontmap = {'rm'  : type_family.roman,
                        'it'  : type_family.italic,
                        'bf'  : type_family.bold,
                        'sf'  : type_family.sans,
                        'tt'  : type_family.mono,
                        'cal' : type_family.cal,
                        None  : type_family.symbol,
                        'fb'  : type_family.fallback
                        }

        for font in self.fontmap.values():
            font.psFont.metrics.fname = font.filename

##        self.fonts['default'] = self.fontmap['rm']
##        self.fonts['regular'] = self.fontmap['rm']

    def _get_font(self, font):
        psg_doc = self.styled.document.backend_document.psg_doc
        psg_doc.add_font(self.fontmap[font].psFont)
        return self.fontmap[font].psFont

    def _get_info(self, fontname, font_class, sym, fontsize, dpi):
        'load the cmfont, metrics and glyph with caching'
        key = fontname, sym, fontsize, dpi
        tup = self.glyphd.get(key)

        if tup is not None:
            return tup

        # Only characters in the "Letter" class should really be italicized.
        # This class includes greek letters, so we're ok
        if (fontname == 'it' and
            (len(sym) > 1 or
             not unicodedata.category(str(sym)).startswith("L"))):
            fontname = 'rm'

        found_symbol = False

        glyph = 'glyph__dummy'
        try:
            num = get_unicode_index(sym)
            found_symbol = True
        except ValueError:
            warn("No TeX to unicode mapping for '{}'".format(sym),
                 MathTextWarning)

        slanted = (fontname == 'it')
        font = self._get_font(fontname)
        font_metrics =font.metrics

        if found_symbol:
            try:
                char_metrics = font_metrics[num]
                symbol_name = char_metrics.ps_name
            except KeyError:
                warn("No glyph in font '{}' for '{}'"
                     .format(font.ps_name, sym), MathTextWarning)
                try:
                    font = self._get_font('fb')
                    font_metrics =font.metrics
                    char_metrics = font_metrics[num]
                    symbol_name = char_metrics.ps_name
                except KeyError:
                    warn("No glyph in font '{}' for '{}'"
                         .format(font.ps_name, sym), MathTextWarning)
                    found_symbol = False

        if not found_symbol:
            try:
                glyph = sym = '?'
                num = ord(glyph)
                char_metrics = font_metrics[num]
                symbol_name = char_metrics.ps_name
            except KeyError:
                num, char_metrics = list(font_metrics.items())[0]
                glyph = sym = chr(num)
                symbol_name = char_metrics.ps_name

        offset = 0

        scale = 0.001 * fontsize

        char_bounding_box = char_metrics.bounding_box.as_tuple()
        xmin, ymin, xmax, ymax = [val * scale for val in char_bounding_box]
        metrics = Bunch(
            advance  = char_metrics.width * scale,
            width    = char_metrics.width * scale,
            height   = ymax * scale,
            xmin = xmin,
            xmax = xmax,
            ymin = ymin + offset,
            ymax = ymax + offset,
            # iceberg is the equivalent of TeX's "height"
            iceberg = ymax + offset,
            slanted = slanted
            )

        self.glyphd[key] = Bunch(
            font            = font_metrics,
            fontsize        = fontsize,
            postscript_name = font.ps_name,
            metrics         = metrics,
            symbol_name     = symbol_name,
            num             = num,
            glyph           = glyph,
            offset          = offset
            )

        return self.glyphd[key]

    def get_kern(self, font1, fontclass1, sym1, fontsize1,
                 font2, fontclass2, sym2, fontsize2, dpi):
        if font1 == font2 and fontsize1 == fontsize2:
            info1 = self._get_info(font1, fontclass1, sym1, fontsize1, dpi)
            info2 = self._get_info(font2, fontclass2, sym2, fontsize2, dpi)
            kerning = info1.font.get_kerning(info1.num, info2.num)
            return kerning * 0.001 * fontsize1
        else:
            return 0.0
            #return Fonts.get_kern(self, font1, fontclass1, sym1, fontsize1,
            #                      font2, fontclass2, sym2, fontsize2, dpi)

    def get_xheight(self, font, fontsize, dpi):
        cached_font = self._get_font(font)
        return cached_font.metrics.FontMetrics['XHeight'] * 0.001 * fontsize

    def get_underline_thickness(self, font, fontsize, dpi):
        cached_font_metrics = self._get_font(font).metrics
        ul_th = (cached_font_metrics.FontMetrics['Direction'][0]
                 ['UnderlineThickness'])
        return ul_th * 0.001 * fontsize
