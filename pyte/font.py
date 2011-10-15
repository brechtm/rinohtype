
import os

from psg.fonts.type1 import type1

class FontStyle:
    Roman = 0   # TODO: rename to 'Regular'?
    Bold = 1
    Italic = 2
    BoldItalic = 3
    Slanted = 4
    BoldSlanted = 5


class Font(object):
    def __init__(self, filename):
        self.filename = filename
        if os.path.exists(filename + ".pfa"):
            self.psFont = type1(filename + ".pfa", filename  + ".afm")
        else:
            self.psFont = type1(filename + ".pfb", filename  + ".afm")
        self.name = self.psFont.full_name


class TypeFace(object):
    def __init__(self, name, roman=None, bold=None, italic=None,
                 bolditalic=None, slanted=None, boldslanted=None):
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

    def __init__(self, serif=None, sans=None, mono=None):
        self.serif = serif
        self.sans = sans
        self.mono = mono
