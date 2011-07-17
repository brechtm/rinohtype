
import os
import unicodedata
from warnings import warn

from psg.fonts.afm_metrics import afm_metrics

from .text import CharacterLike, Box, MixedStyledText, NewLine, Tab, ParentStyle
from .mathtext import Fonts, MathtextBackendPs, MathTextWarning, Parser, Bunch
from ._mathtext_data import latex_to_standard


class Math(CharacterLike):
    #style_class = MathStyle
    _parser = None

    def __init__(self, equation, style=ParentStyle):
        super().__init__(style)
        self.equation = equation

    def characters(self):
        font_output = PsgFonts()
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


class Equation(MixedStyledText):
    next_number = 1

    def __init__(self, equation, style=ParentStyle):
        self.ref = str(self.next_number)
        number = '({})'.format(self.next_number)
        self.__class__.next_number += 1
        #text = [NewLine(), Math(equation), Tab(), number, NewLine()]
        text = [Math(equation), Tab(), number]
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

    basepath = r'W:\code\matplotlib-py3\lib\matplotlib\mpl-data\fonts\afm'

    fontmap = { 'cal' : 'pzcmi8a',  # Zapf Chancery
                'rm'  : 'pncr8a',   # New Century Schoolbook
                'tt'  : 'pcrr8a',   # Courier
                'it'  : 'pncri8a',  # New Century Schoolbook Italic
                'sf'  : 'phvr8a',   # Helvetica
                'bf'  : 'pncb8a',   # New Century Schoolbook Bold
                None  : 'psyr'      # Symbol
                }

    def __init__(self):
        Fonts.__init__(self, None, MathtextBackendPs())
        self.glyphd = {}
        self.fonts = {}

        filename = os.path.join(self.basepath, 'phvr8a.afm')
        # TODO: change to use type1 instead of afm_metrics
        default_font = afm_metrics(open(filename, 'rb'))
        default_font.fname = filename

        self.fonts['default'] = default_font
        self.fonts['regular'] = default_font

    def _get_font(self, font):
        if font in self.fontmap:
            basename = self.fontmap[font]
        else:
            basename = font

        cached_font = self.fonts.get(basename)
        if cached_font is None:
            fname = os.path.join(self.basepath, basename + ".afm")
            cached_font = afm_metrics(open(fname, 'rb'))
            cached_font.fname = fname
            self.fonts[basename] = cached_font
            self.fonts[cached_font.FontMetrics['FontName']] = cached_font
        return cached_font

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

        if sym in latex_to_standard:
            fontname, num = latex_to_standard[sym]
            glyph = chr(num)
            found_symbol = True
        elif len(sym) == 1:
            glyph = sym
            num = ord(glyph)
            found_symbol = True
        else:
            warn("No TeX to built-in Postscript mapping for '{}'".format(sym),
                 MathTextWarning)

        slanted = (fontname == 'it')
        font = self._get_font(fontname)

        if found_symbol:
            try:
                char_metrics = font.FontMetrics["Direction"][0]["CharMetrics"][num]
                symbol_name = char_metrics["N"]
            except KeyError:
                warn("No glyph in standard Postscript font '{}' for '{}'"
                     .format(font.FontMetrics["FontName"], sym), MathTextWarning)
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
            kerning_pairs = info1.font.kerning_pairs
            kerning = kerning_pairs.get((info1.num, info2.num), 0.0)
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
