"""Adobe PDF core font set"""

import os

from . import fonts_path
from ..font import Font, TypeFace, TypeFamily


directory = os.path.join(fonts_path, 'adobe14')


courier_r = Font(os.path.join(directory, 'Courier'), True)
courier_b = Font(os.path.join(directory, 'Courier-Bold'), True)
courier_bo = Font(os.path.join(directory, 'Courier-BoldOblique'), True)
courier_o = Font(os.path.join(directory, 'Courier-Oblique'), True)

helvetica_r = Font(os.path.join(directory, 'Helvetica'), True)
helvetica_b = Font(os.path.join(directory, 'Helvetica-Bold'), True)
helvetica_bo = Font(os.path.join(directory, 'Helvetica-BoldOblique'), True)
helvetica_o = Font(os.path.join(directory, 'Helvetica-Oblique'), True)

symbol_r = Font(os.path.join(directory, 'Symbol'), True)

times_r = Font(os.path.join(directory, 'Times-Roman'), True)
times_b = Font(os.path.join(directory, 'Times-Bold'), True)
times_bi = Font(os.path.join(directory, 'Times-BoldItalic'), True)
times_i = Font(os.path.join(directory, 'Times-Italic'), True)

zapfdingbats_r = Font(os.path.join(directory, 'ZapfDingbats'), True)


courier = TypeFace('Courier', courier_r, courier_b, courier_o, courier_bo)
helvetica = TypeFace('Helvetica', helvetica_r, helvetica_b, helvetica_o,
                     helvetica_bo)
symbol = TypeFace('Symbol', symbol_r)
times = TypeFace('Times', times_r, times_b, times_i, times_bi)
zapfdingbats = TypeFace('ZapfDingbats', zapfdingbats_r)


# 'Adobe PDF Core Font Set'
family = TypeFamily(times, helvetica, courier)
