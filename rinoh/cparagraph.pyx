# cython: language_level=3
# cython: profile=True


cdef class GlyphsSpan(list):
    def __cinit__(self, span, word_to_glyphs):
        self.span = span
        self.filled_tabs = {}
        self.word_to_glyphs = word_to_glyphs
        self.number_of_spaces = 0
        self.space_glyph_and_width = list(word_to_glyphs(' ')[0])

    def __init__(self, span, word_to_glyphs):
        super().__init__()

    def append_space(self):
        self.number_of_spaces += 1
        self.append(self.space_glyph_and_width)

    #def _fill_tabs(self):
    #    for index, glyph_and_width in enumerate(super().__iter__()):
    #        if index in self.filled_tabs:
    #            fill_string = self.filled_tabs[index]
    #            tab_width = glyph_and_width[1]
    #            fill_glyphs = self.word_to_glyphs(fill_string)
    #            fill_string_width = sum(width for glyph, width in fill_glyphs)
    #            number, rest = divmod(tab_width, fill_string_width)
    #            yield glyph_and_width[0], rest
    #            for i in range(int(number)):
    #                for fill_glyph_and_width in fill_glyphs:
    #                    yield fill_glyph_and_width
    #        else:
    #            yield glyph_and_width

    #def __iter__(self):
    #    if self.filled_tabs:
    #        return self._fill_tabs()
    #    else:
    #        return super().__iter__()
