

class GlyphMetrics(object):
    def __init__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code


class FontMetrics(dict):
    def get_glyph(self, char, variant=None):
        raise NotImplementedError

    def get_ligature(self, glyph, successor_glyph):
        raise NotImplementedError

    def get_kerning(self, a, b):
        raise NotImplementedError
