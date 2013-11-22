
cdef class GlyphMetrics(object):
    cdef public unicode name
    cdef public int width
    cdef public tuple bounding_box
    cdef public int code
