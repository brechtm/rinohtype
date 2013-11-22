# cython: language_level=3
# cython: profile=True


cdef class GlyphMetrics(object):
    def __cinit__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code
