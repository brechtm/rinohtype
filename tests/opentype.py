
import time

from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import SMALL_CAPITAL


if __name__ == '__main__':
    time.clock()
    ot = OpenTypeFont('texgyretermes-regular.otf')
    ot2 = OpenTypeFont('Cuprum.otf')
    ot3 = OpenTypeFont('Puritan2.otf')

    print(ot.get_kerning(ot.get_glyph_metrics('V'), ot.get_glyph_metrics('A')))
    print(ot2.get_kerning(ot2.get_glyph_metrics('U'), ot2.get_glyph_metrics('A')))
    print(ot.get_ligature(ot.get_glyph_metrics('f'), ot.get_glyph_metrics('f')))
    print(ot.get_ligature(ot.get_glyph_metrics('f'), ot.get_glyph_metrics('i')))
    print(ot.get_ligature(ot.get_glyph_metrics('f'), ot.get_glyph_metrics('i')))
    print(ot.get_glyph_metrics('s').code, ot.get_glyph_metrics('s', SMALL_CAPITAL).code)
    run_time = time.clock()
    print('Total execution time: {} seconds'.format(run_time))
