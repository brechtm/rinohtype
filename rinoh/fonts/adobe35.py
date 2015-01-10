# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""Adobe PostScript core font set"""

import os

from . import FONTS_PATH
from ..font import TypeFace, TypeFamily
from ..font.type1 import Type1Font
from ..font.style import LIGHT, BOOK, REGULAR, MEDIUM, DEMI_BOLD, BOLD
from ..font.style import OBLIQUE, ITALIC, CONDENSED
from ..math import MathFonts


__all__ = ['avantgarde', 'bookman', 'courier', 'helvetica', 'newcenturyschlbk',
           'palatino', 'symbol', 'times', 'zapfchancery', 'zapfdingbats']


def path(name):
    return os.path.join(FONTS_PATH, 'adobe35', name)


avantgarde = TypeFace('ITC Avant Garde Gothic',
                      Type1Font(path('ITCAvantGarde-Book'), weight=BOOK,
                                core=True),
                      Type1Font(path('ITCAvantGarde-BookOblique'), weight=BOOK,
                                slant=OBLIQUE, core=True),
                      Type1Font(path('ITCAvantGarde-Demi'), weight=DEMI_BOLD,
                                core=True),
                      Type1Font(path('ITCAvantGarde-DemiOblique'),
                                weight=DEMI_BOLD, slant=OBLIQUE, core=True))

bookman = TypeFace('ITC Bookman',
                   Type1Font(path('ITCBookman-Light'), weight=LIGHT, core=True),
                   Type1Font(path('ITCBookman-LightItalic'), weight=LIGHT,
                             slant=ITALIC, core=True),
                   Type1Font(path('ITCBookman-Demi'), weight=DEMI_BOLD,
                             core=True),
                   Type1Font(path('ITCBookman-DemiItalic'), weight=DEMI_BOLD,
                             slant=ITALIC, core=True))

courier = TypeFace('Courier',
                   Type1Font(path('Courier'), core=True),
                   Type1Font(path('Courier-Oblique'), slant=OBLIQUE, core=True),
                   Type1Font(path('Courier-Bold'), weight=BOLD, core=True),
                   Type1Font(path('Courier-BoldOblique'), weight=BOLD,
                             slant=OBLIQUE, core=True))

helvetica = TypeFace('Helvetica',
                     Type1Font(path('Helvetica'), core=True),
                     Type1Font(path('Helvetica-Oblique'), slant=OBLIQUE,
                               core=True),
                     Type1Font(path('Helvetica-Bold'), weight=BOLD, core=True),
                     Type1Font(path('Helvetica-BoldOblique'), weight=BOLD,
                               slant=OBLIQUE, core=True),
                     Type1Font(path('Helvetica-Narrow'), width=CONDENSED,
                               core=True),
                     Type1Font(path('Helvetica-NarrowOblique'), width=CONDENSED,
                               slant=OBLIQUE, core=True),
                     Type1Font(path('Helvetica-NarrowBold'), width=CONDENSED,
                               weight=BOLD, core=True),
                     Type1Font(path('Helvetica-NarrowBoldOblique'),
                               width=CONDENSED, weight=BOLD, slant=OBLIQUE,
                               core=True))

newcenturyschlbk = TypeFace('New Century Schoolbook',
                            Type1Font(path('NewCenturySchlbk-Roman'),
                                      core=True),
                            Type1Font(path('NewCenturySchlbk-Italic'),
                                      slant=ITALIC, core=True),
                            Type1Font(path('NewCenturySchlbk-Bold'),
                                      weight=BOLD, core=True),
                            Type1Font(path('NewCenturySchlbk-BoldItalic'),
                                      weight=BOLD, slant=ITALIC, core=True))

palatino = TypeFace('Palatino',
                    Type1Font(path('Palatino-Roman'), core=True),
                    Type1Font(path('Palatino-Italic'), slant=ITALIC, core=True),
                    Type1Font(path('Palatino-Bold'), weight=BOLD, core=True),
                    Type1Font(path('Palatino-BoldItalic'), weight=BOLD,
                              slant=ITALIC, core=True))

symbol = TypeFace('Symbol', Type1Font(path('Symbol'), core=True))

times = TypeFace('Times',
                 Type1Font(path('Times-Roman'), weight=REGULAR, core=True),
                 Type1Font(path('Times-Italic'), slant=ITALIC, core=True),
                 Type1Font(path('Times-Bold'), weight=BOLD, core=True),
                 Type1Font(path('Times-BoldItalic'), weight=BOLD, slant=ITALIC,
                           core=True))

zapfchancery = TypeFace('ITC Zapf Chancery',
                        Type1Font(path('ITCZapfChancery-MediumItalic'),
                                  slant=ITALIC, core=True))

zapfdingbats = TypeFace('ITC ZapfDingbats',
                        Type1Font(path('ZapfDingbats'), core=True))


postscript_mathfonts = MathFonts(newcenturyschlbk.get_font(),
                                 newcenturyschlbk.get_font(slant=ITALIC),
                                 newcenturyschlbk.get_font(weight=BOLD),
                                 helvetica.get_font(),
                                 courier.get_font(),
                                 zapfchancery.get_font(slant=ITALIC),
                                 symbol.get_font(),
                                 symbol.get_font())
