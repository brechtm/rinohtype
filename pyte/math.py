
import os
import unicodedata
from warnings import warn

from pyte.font import FontStyle
from psg.fonts.afm_metrics import afm_metrics

from .unit import pt
from .font import TypeFamily
from .text import ParentStyle, Style, CharacterLike, Box, NewLine, Tab
from .text import MixedStyledText
from .paragraph import ParagraphStyle
from .mathtext import Fonts, MathtextBackendPs, MathTextWarning, Parser, Bunch
from .mathtext import get_unicode_index
from ._mathtext_data import tex2uni


class MathFonts(object):
    default = None

    def __init__(self, roman, italic, bold, sans, mono, cal, symbol, fallback):
        self.roman = symbol
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
        font_output = PsgFonts(self)
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
    attributes = {'math_style': None}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Equation(MixedStyledText):
    style_class = EquationStyle
    next_number = 1

    def __init__(self, equation, style=None):
        self.ref = str(self.next_number)
        number = '({})'.format(self.next_number)
        self.__class__.next_number += 1
        math = Math(equation, style=style.math_style)
        math.parent = self # TODO: encapsulate
        #math.document = self.document
        #text = [NewLine(), Math(equation), Tab(), number, NewLine()]
        text = [math, Tab(), number]
        super().__init__(text, style)

    def reference(self):
        return self.ref


# adapted from matplotlib.mathtext.StandardPsFonts
class PsgFonts(Fonts):
    """
    Use the standard postscript fonts for rendering to backend_ps

    Unlike the other font classes, BakomaFont and UnicodeFont, this
    one requires the Ps backend.
    """
    def __init__(self, styled):
        Fonts.__init__(self, None, MathtextBackendPs())
        self.styled = styled
        self.glyphd = {}
        self.fonts = {}

        #filename = os.path.join(self.basepath, 'phvr8a.afm')
        #default_font = afm_metrics(open(filename, 'rb'))
        #default_font.fname = filename

        type_family = self.styled.get_style('fonts')
        self.fontmap = {'cal' : type_family.cal,
                        'rm'  : type_family.roman,
                        'tt'  : type_family.mono,
                        'it'  : type_family.italic,
                        'sf'  : type_family.sans,
                        'bf'  : type_family.bold,
                        None  : type_family.symbol,
                        'fb'  : type_family.fallback
                        }

        for font in self.fontmap.values():
            font.psFont.metrics.fname = font.filename

        self.fonts['default'] = self.fontmap['rm']
        self.fonts['regular'] = self.fontmap['rm']

    def _get_font(self, font):
        return self.fontmap[font].psFont.metrics

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
        #self.document.dsc_doc.add_font(font)
        #font_wrapper = canvas.page.register_font(font.psFont, True)

        if found_symbol:
            try:
                char_metrics = font.FontMetrics["Direction"][0]["CharMetrics"][num]
                symbol_name = char_metrics["N"]
            except KeyError:
                warn("No glyph in Postscript font '{}' for '{}'"
                     .format(font.FontMetrics['FontName'], sym), MathTextWarning)
                try:
                    font = self._get_font('fb')
                    char_metrics = font.FontMetrics["Direction"][0]["CharMetrics"][num]
                    symbol_name = char_metrics["N"]
                except KeyError:
                    warn("No glyph in Postscript font '{}' for '{}'"
                         .format(font.FontMetrics['FontName'], sym), MathTextWarning)
                    found_symbol = False

        if not found_symbol:
            glyph = sym = '?'
            num = ord(glyph)
            char_metrics = font.FontMetrics["Direction"][0]["CharMetrics"][num]
            symbol_name = char_metrics["N"]

        offset = 0

        scale = 0.001 * fontsize

        xmin, ymin, xmax, ymax = [val * scale for val in char_metrics["B"]]
        metrics = Bunch(
            advance  = char_metrics["WX"] * scale,
            width    = char_metrics["WX"] * scale,
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
            font            = font,
            fontsize        = fontsize,
            postscript_name = font.FontMetrics['FontName'],
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
        return cached_font.FontMetrics['XHeight'] * 0.001 * fontsize

    def get_underline_thickness(self, font, fontsize, dpi):
        cached_font = self._get_font(font)
        ul_th = cached_font.FontMetrics['Direction'][0]['UnderlineThickness']
        return ul_th * 0.001 * fontsize
