

class GlyphMetrics(object):
    def __init__(self, name, width, bounding_box, code):
        self.name = name
        self.width = width
        self.bounding_box = bounding_box
        self.code = code


class FontMetrics(dict):
    def __init__(self):
        self.glyphs = {}
        self.ligatures = {}
        self.kerning_pairs = {}

    def get_kerning(self, a, b):
        return self.kerning_pairs.get((a, b), 0.0)