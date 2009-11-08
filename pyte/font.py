
from psg.fonts.type1 import type1

class FontStyle:
    Roman = 0
    Bold = 1
    Italic = 2
    BoldItalic = 3
    Slanted = 4
    BoldSlanted = 5

class Font(object):
    # TODO: encoding conversion as in pypsg (change pslib?)
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.psFont = type1(filename + ".pfb", filename  + ".afm")

    #def loadFont(self, psdoc):
    #    if psdoc not in self.PSFont:
    #        self.PSFont[psdoc] = PS_findfont(psdoc, self.filename, "", 1)
    #    return self.PSFont[psdoc]


class TypeFace(object):
    def __init__(self, name, roman=None, bold=None, italic=None, bolditalic=None, slanted=None, boldslanted=None):
        #assert isinstance(roman, Font)
        #assert isinstance(bold, Font)
        #assert isinstance(italic, Font)
        #assert isinstance(bolditalic, Font)
        #assert isinstance(slanted, Font)
        #assert isinstance(boldslanted, Font)
        #assert isinstance(smallcaps, Font)
        self.fontStyles = {}
        self.name = name
        self.roman = roman
        self.fontStyles[FontStyle.Roman] = roman
        self.bold = bold
        self.fontStyles[FontStyle.Bold] = bold
        self.italic = italic
        self.fontStyles[FontStyle.Italic] = italic
        self.bolditalic = bolditalic
        self.fontStyles[FontStyle.BoldItalic] = bolditalic
        self.slanted = slanted
        self.fontStyles[FontStyle.Slanted] = slanted
        self.boldslanted = boldslanted
        self.fontStyles[FontStyle.BoldSlanted] = boldslanted
        
    def font(self, style):
        return self.fontStyles[style]


class TypeFamily(object):
    default = None
    
    def __init__(self, serif=None, sans=None, mono=None, math=None):
        #assert isinstance(serif, TypeFace)
        #assert isinstance(sans, TypeFace)
        #assert isinstance(mono, TypeFace)
        #assert isinstance(math, TypeFace)
        self.serif = serif
        self.sans  = sans
        self.mono  = mono
        self.math  = math

    def setDefault(cls, typefamily):
        TypeFamily.default = typefamily
    setDefault = classmethod(setDefault)

