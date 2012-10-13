
import time

from pyte.font.opentype import OpenTypeFont
from pyte.font.style import SMALL_CAPITAL


if __name__ == '__main__':
    time.clock()
    ot = OpenTypeFont('texgyretermes-regular.otf')
    ot2 = OpenTypeFont('Cuprum.otf')
    ot3 = OpenTypeFont('Puritan2.otf')

    print(ot.metrics.get_kerning(ot.metrics.get_glyph('V'), ot.metrics.get_glyph('A')))
    print(ot2.metrics.get_kerning(ot2.metrics.get_glyph('U'), ot2.metrics.get_glyph('A')))
    print(ot.metrics.get_ligature(ot.metrics.get_glyph('f'), ot.metrics.get_glyph('f')))
    print(ot.metrics.get_ligature(ot.metrics.get_glyph('f'), ot.metrics.get_glyph('i')))
    print(ot.metrics.get_ligature(ot.metrics.get_glyph('f'), ot.metrics.get_glyph('i')))
    print(ot.metrics.get_glyph('s').code, ot.metrics.get_glyph('s', SMALL_CAPITAL).code)
    run_time = time.clock()
    print('Total execution time: {} seconds'.format(run_time))
