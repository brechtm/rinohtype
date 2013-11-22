# cython: language_level=3


from . import cos


def show_glyphs(object self, left, cursor, glyph_span):
    span = glyph_span.span
    font = span.font
    size = span.height
    font_rsc, font_name = self.cos_page.register_font(font)
    string = ''
    current_string = ''
    total_width = 0
    for glyph, width in glyph_span:
        total_width += width
        displ = (1000 * width) / size
        code = glyph.code
        if font.encoding:
            if code < 0:
                try:
                    differences = font_rsc['Encoding']['Differences']
                except KeyError:
                    occupied = list(font.encoding.values())
                    differences = cos.EncodingDifferences(occupied)
                    font_rsc['Encoding']['Differences'] = differences
                code = differences.register(glyph)
            char = CODE_TO_CHAR[code]
        else:
            high, low = code >> 8, code & 0xFF
            char = CODE_TO_CHAR[high] + CODE_TO_CHAR[low]
        adjust = int(glyph.width - displ)
        if adjust:
            string += '({}{}) {} '.format(current_string, char,
                                          adjust)
            current_string = ''
        else:
            current_string += char
    if current_string:
        string += '({})'.format(current_string)
    print('BT', file=self)
    print('/{} {} Tf'.format(font_name, size), file=self)
    print('{} {} Td'.format(left, - (cursor - span.y_offset)), file=self)
    print('[{}] TJ'.format(string), file=self)
    print('ET', file=self)
    return total_width


CODE_TO_CHAR = {}


def _code_to_char(code):
    if code < 32 or code > 127:
        char = '\{:03o}'.format(code)
    else:
        char = chr(code)
        if char in ('\\', '(', ')'):
            char = '\\' + char
    return char


for code in range(256):
    CODE_TO_CHAR[code] = _code_to_char(code)
