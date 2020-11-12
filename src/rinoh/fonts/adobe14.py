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


def type1(name, **kwargs):
    path = os.path.join(FONTS_PATH, 'adobe14', name)
    return Type1Font(path, core=True, **kwargs)


courier = Typeface('Courier',
                   type1('Courier'),
                   type1('Courier-Oblique', slant=OBLIQUE),
                   type1('Courier-Bold', weight=BOLD),
                   type1('Courier-BoldOblique', weight=BOLD, slant=OBLIQUE))

helvetica = Typeface('Helvetica',
                     type1('Helvetica'),
                     type1('Helvetica-Oblique', slant=OBLIQUE),
                     type1('Helvetica-Bold', weight=BOLD),
                     type1('Helvetica-BoldOblique', weight=BOLD, slant=OBLIQUE))

symbol = Typeface('Symbol', type1('Symbol'))

times = Typeface('Times',
                 type1('Times-Roman', weight=REGULAR),
                 type1('Times-Italic', slant=ITALIC),
                 type1('Times-Bold', weight=BOLD),
                 type1('Times-BoldItalic', weight=BOLD, slant=ITALIC))

zapfdingbats = Typeface('ITC ZapfDingbats',
                        type1('ZapfDingbats',
                              unicode_mapping=UNICODE_TO_DINGBATS_NAME))

# 'Adobe PDF Core Font Set'
pdf_family = TypeFamily(serif=times, sans=helvetica, mono=courier,
                        symbol=symbol, dingbats=zapfdingbats)
