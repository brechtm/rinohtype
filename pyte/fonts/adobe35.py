"""Adobe PostScript core font set"""

import os

from . import FONTS_PATH
from ..font import Font, TypeFace, TypeFamily
from ..font.style import LIGHT, BOOK, REGULAR, MEDIUM, DEMI_BOLD, BOLD
from ..font.style import OBLIQUE, ITALIC, CONDENSED
from ..math import MathFonts


__all__ = ['avantgarde', 'bookman', 'courier', 'helvetica', 'newcenturyschlbk',
           'palatino', 'symbol', 'times', 'zapfchancery', 'zapfdingbats']


def path(name):
    return os.path.join(FONTS_PATH, 'adobe35', name)


avantgarde = TypeFace('ITC Avant Garde Gothic',
                      Font(path('ITCAvantGarde-Book'), weight=BOOK, core=True),
                      Font(path('ITCAvantGarde-BookOblique'), weight=BOOK,
                           slant=OBLIQUE, core=True),
                      Font(path('ITCAvantGarde-Demi'), weight=DEMI_BOLD,
                           core=True),
                      Font(path('ITCAvantGarde-DemiOblique'), weight=DEMI_BOLD,
                           slant=OBLIQUE, core=True))

bookman = TypeFace('ITC Bookman',
                   Font(path('ITCBookman-Light'), weight=LIGHT, core=True),
                   Font(path('ITCBookman-LightItalic'), weight=LIGHT,
                             slant=ITALIC, core=True),
                   Font(path('ITCBookman-Demi'), weight=DEMI_BOLD, core=True),
                   Font(path('ITCBookman-DemiItalic'), weight=DEMI_BOLD,
                             slant=ITALIC, core=True))

courier = TypeFace('Courier',
                   Font(path('Courier'), core=True),
                   Font(path('Courier-Oblique'), slant=OBLIQUE, core=True),
                   Font(path('Courier-Bold'), weight=BOLD, core=True),
                   Font(path('Courier-BoldOblique'), weight=BOLD, slant=OBLIQUE,
                        core=True))

helvetica = TypeFace('Helvetica',
                     Font(path('Helvetica'), core=True),
                     Font(path('Helvetica-Oblique'), slant=OBLIQUE, core=True),
                     Font(path('Helvetica-Bold'), weight=BOLD, core=True),
                     Font(path('Helvetica-BoldOblique'), weight=BOLD,
                          slant=OBLIQUE, core=True),
                     Font(path('Helvetica-Narrow'), width=CONDENSED, core=True),
                     Font(path('Helvetica-NarrowOblique'), width=CONDENSED,
                          slant=OBLIQUE, core=True),
                     Font(path('Helvetica-NarrowBold'), width=CONDENSED,
                          weight=BOLD, core=True),
                     Font(path('Helvetica-NarrowBoldOblique'), width=CONDENSED,
                          weight=BOLD, slant=OBLIQUE, core=True))

newcenturyschlbk = TypeFace('New Century Schoolbook',
                            Font(path('NewCenturySchlbk-Roman'), core=True),
                            Font(path('NewCenturySchlbk-Italic'), slant=ITALIC,
                                 core=True),
                            Font(path('NewCenturySchlbk-Bold'), weight=BOLD,
                                 core=True),
                            Font(path('NewCenturySchlbk-BoldItalic'),
                                 weight=BOLD, slant=ITALIC, core=True))

palatino = TypeFace('Palatino',
                    Font(path('Palatino-Roman'), core=True),
                    Font(path('Palatino-Italic'), slant=ITALIC, core=True),
                    Font(path('Palatino-Bold'), weight=BOLD, core=True),
                    Font(path('Palatino-BoldItalic'), weight=BOLD, slant=ITALIC,
                         core=True))

symbol = TypeFace('Symbol', Font(path('Symbol'), core=True))

times = TypeFace('Times',
                 Font(path('Times-Roman'), weight=REGULAR, core=True),
                 Font(path('Times-Italic'), slant=ITALIC, core=True),
                 Font(path('Times-Bold'), weight=BOLD, core=True),
                 Font(path('Times-BoldItalic'), weight=BOLD, slant=ITALIC,
                      core=True))

zapfchancery = TypeFace('ITC Zapf Chancery',
                        Font(path('ITCZapfChancery-MediumItalic'), slant=ITALIC,
                             core=True))

zapfdingbats = TypeFace('ITC ZapfDingbats',
                        Font(path('ZapfDingbats'), core=True))


postscript_mathfonts = MathFonts(newcenturyschlbk.get(),
                                 newcenturyschlbk.get(slant=ITALIC),
                                 newcenturyschlbk.get(weight=BOLD),
                                 helvetica.get(),
                                 courier.get(),
                                 zapfchancery.get(slant=ITALIC),
                                 symbol.get(),
                                 symbol.get())
