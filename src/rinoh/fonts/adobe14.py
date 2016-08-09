# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""Adobe PDF core font set"""

import os

from . import FONTS_PATH
from ..font import Typeface, TypeFamily
from ..font.mapping import UNICODE_TO_DINGBATS_NAME
from ..font.type1 import Type1Font
from ..font.style import REGULAR, BOLD, OBLIQUE, ITALIC



def path(name):
    return os.path.join(FONTS_PATH, 'adobe14', name)


courier = Typeface('Courier',
                   Type1Font(path('Courier'), core=True),
                   Type1Font(path('Courier-Oblique'), slant=OBLIQUE, core=True),
                   Type1Font(path('Courier-Bold'), weight=BOLD, core=True),
                   Type1Font(path('Courier-BoldOblique'), weight=BOLD,
                             slant=OBLIQUE, core=True))

helvetica = Typeface('Helvetica',
                     Type1Font(path('Helvetica'), core=True),
                     Type1Font(path('Helvetica-Oblique'), slant=OBLIQUE,
                               core=True),
                     Type1Font(path('Helvetica-Bold'), weight=BOLD, core=True),
                     Type1Font(path('Helvetica-BoldOblique'), weight=BOLD,
                               slant=OBLIQUE, core=True))

symbol = Typeface('Symbol', Type1Font(path('Symbol'), core=True))

times = Typeface('Times',
                 Type1Font(path('Times-Roman'), weight=REGULAR, core=True),
                 Type1Font(path('Times-Italic'), slant=ITALIC, core=True),
                 Type1Font(path('Times-Bold'), weight=BOLD, core=True),
                 Type1Font(path('Times-BoldItalic'), weight=BOLD, slant=ITALIC,
                           core=True))

zapfdingbats = Typeface('ITC ZapfDingbats',
                        Type1Font(path('ZapfDingbats'), core=True,
                                  unicode_mapping=UNICODE_TO_DINGBATS_NAME))

# 'Adobe PDF Core Font Set'
pdf_family = TypeFamily(serif=times, sans=helvetica, mono=courier,
                        symbol=symbol, dingbats=zapfdingbats)
