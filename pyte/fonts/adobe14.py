"""Adobe PDF core font set"""

import os

from . import fonts_path
from ..font import Font, TypeFace, TypeFamily
from ..font.style import REGULAR, MEDIUM, BOLD, OBLIQUE, ITALIC, CONDENSED



def path(name):
    return os.path.join(fonts_path, 'adobe14', name)


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
                          slant=OBLIQUE, core=True))

symbol = TypeFace('Symbol', Font(path('Symbol'), core=True))

times = TypeFace('Times',
                 Font(path('Times-Roman'), weight=REGULAR, core=True),
                 Font(path('Times-Italic'), slant=ITALIC, core=True),
                 Font(path('Times-Bold'), weight=BOLD, core=True),
                 Font(path('Times-BoldItalic'), weight=BOLD, slant=ITALIC,
                      core=True))

zapfdingbats = TypeFace('ITC ZapfDingbats', Font(path('ZapfDingbats'),
                        core=True))

# 'Adobe PDF Core Font Set'
family = TypeFamily(serif=times, sans=helvetica, mono=courier,
                    symbol=symbol, dingbats=zapfdingbats)
