# cython: language_level=3
# cython: profile=True

import cython

from libcpp cimport bool

from . import cos


from rinoh.cparagraph cimport GlyphsSpan
from rinoh.font.glyphmetrics cimport GlyphMetrics


@cython.boundscheck(False)
def show_glyphs(object self, int left, unsigned int cursor, GlyphsSpan glyph_span):
    span = glyph_span.span
    font = span.font
    cdef int font_has_encoding = font.encoding is not None
    cdef float size = span.height
    cdef float y_offset = span.y_offset
    font_rsc, font_name = self.cos_page.register_font(font)
    cdef unicode string = ''
    cdef unicode current_string = ''
    cdef float total_width = 0
    cdef float width
    cdef int displ
    cdef unicode uni_char
    cdef int adjust
    cdef GlyphMetrics glyph
    for glyph, width in glyph_span:
        total_width += width
        displ = <int> ((1000.0 * width) / size)
        if font_has_encoding:
            if glyph.code < 0:
                try:
                    differences = font_rsc['Encoding']['Differences']
                except KeyError:
                    occupied = list(font.encoding.values())
                    differences = cos.EncodingDifferences(occupied)
                    font_rsc['Encoding']['Differences'] = differences
                code = differences.register(glyph)
            uni_char = CODE_TO_CHAR[glyph.code]
        else:
            high, low = glyph.code >> 8, glyph.code & 0xFF
            uni_char = CODE_TO_CHAR[high] + CODE_TO_CHAR[low]
        adjust = glyph.width - displ
        if adjust:
            string += '({}{}) {} '.format(current_string, uni_char, adjust)
            current_string = ''
        else:
            current_string += uni_char
    if current_string:
        string += '({})'.format(current_string)
    print('BT', file=self)
    print('/{} {} Tf'.format(font_name, size), file=self)
    print('{} {} Td'.format(left, - (cursor - y_offset)), file=self)
    print('[{}] TJ'.format(string), file=self)
    print('ET', file=self)
    return total_width


cdef list CODE_TO_CHAR = 256 * [None]


cdef unsigned int code
for code in range(256):
    uni_str = _code_to_char(code)
    CODE_TO_CHAR[code] = uni_str


cdef _code_to_char(unsigned char code):
    cdef unicode char_repr
    if code < 32 or code > 127:
        char_repr = '\{:03o}'.format(code)
    else:
        char_repr = chr(code)
        if char_repr in ('\\', '(', ')'):
            char_repr = '\\' + char_repr
    return char_repr
