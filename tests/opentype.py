
import time

from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import SMALL_CAPITAL


if __name__ == '__main__':
    time.clock()
    ot = OpenTypeFont('texgyretermes-regular.otf')
    ot2 = OpenTypeFont('Cuprum.otf')
    ot3 = OpenTypeFont('Puritan2.otf')

    print(ot.get_kerning(ot.get_glyph('V'), ot.get_glyph('A')))
    print(ot2.get_kerning(ot2.get_glyph('U'), ot2.get_glyph('A')))
    print(ot.get_ligature(ot.get_glyph('f'), ot.get_glyph('f')))
    print(ot.get_ligature(ot.get_glyph('f'), ot.get_glyph('i')))
    print(ot.get_ligature(ot.get_glyph('f'), ot.get_glyph('i')))
    print(ot.get_glyph('s').code, ot.get_glyph('s', SMALL_CAPITAL).code)
    run_time = time.clock()
    print('Total execution time: {} seconds'.format(run_time))
