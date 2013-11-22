

cdef class GlyphsSpan(list):
    cdef public object span
    cdef public list space_glyph_and_width
    cdef public int number_of_spaces
    cdef public dict filled_tabs

    cdef object word_to_glyphs

