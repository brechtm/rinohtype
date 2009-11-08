
from pyte.unit import pt
from pyte.font import TypeFace, FontStyle

class TextStyle(object):
    default = None

    def __init__(self, typeface=None, fontStyle=None, fontSize=None,
                        smallCaps=None,
                        hyphenate=None, hyphenChars=None, hyphenLang=None,
                        base=None):
        if typeface is not None:
            assert isinstance(typeface, TypeFace)
            self.typeface = typeface
        if fontStyle is not None: self.fontStyle = fontStyle
        if fontSize is not None: self.fontSize = fontSize
        if smallCaps is not None: self.smallCaps = smallCaps
        if hyphenate is not None: self.hyphenate = hyphenate
        if hyphenChars is not None: self.hyphenChars = hyphenChars
        if hyphenLang is not None: self.hyphenLang = hyphenLang
        if base:
            assert isinstance(base, TextStyle)
            self.base = base
        else:
            self.base = TextStyle.default

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.base.__getattribute__(name)


##TextStyle.default = TextStyle(typeface = None,
##                                fontStyle = FontStyle.Roman,
##                                fontSize = 10*pt, # TODO: change default
##                                smallCaps = False,
##                                hyphenate = True,
##                                hyphenChars = 2,
##                                hyphenLang = "en")

class DefaultStyle:
    pass

class Text(object):
    def __init__(self, text, style=TextStyle.default):
        self.text = text
        if style == DefaultStyle:
            self.style = TextStyle.default
        else:
            self.style = style


##emStyle = TextStyle(fontStyle=FontStyle.Italic)
##boldStyle = TextStyle(fontStyle=FontStyle.Bold)
##italicStyle = TextStyle(fontStyle=FontStyle.Italic)
##
##class Bold(Text):
##    def __init__(self, text):
##        Text.__init__(self, text, style=boldStyle)
##
##class Italic(Text):
##    def __init__(self, text):
##        Text.__init__(self, text, style=italicStyle)
##
##class Em(Text):
##    def __init__(self, text):
##        Text.__init__(self, text, style=italicStyle)
