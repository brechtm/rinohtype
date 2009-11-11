
from pyte.unit import pt
from pyte.font import TypeFace, FontStyle

class TextStyle(object):
    default = None

    def __init__(self, name="", typeface=None, fontStyle=None, fontSize=None,
                        smallCaps=None,
                        hyphenate=None, hyphenChars=None, hyphenLang=None,
                        base=None):
        self.name = name
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
        if name == 'base':
            if object.__getattribute__(self, name) is None:
                return TextStyle.default
            else:
                return object.__getattribute__(self, name)
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
    def __init__(self, text, style=DefaultStyle):
        self.text = text
        if style == DefaultStyle:
            self.style = TextStyle.default
        else:
            self.style = style

    def __repr__(self):
        return self.text

    def characters(self):
        characters = []
        for character in self.text:
            characters.append(Character(character, style=self.style))

        return characters


# TODO: make following classes immutable (override setattr) and store widths
class Character(Text):
    def __init__(self, text, style=DefaultStyle):
        assert len(text) == 1
        Text.__init__(self, text, style)

    def width(self):
        typeface = self.style.typeface
        font = typeface.font(self.style.fontStyle)
        return font.psFont.metrics.stringwidth(self.text, float(self.style.fontSize))

    def ord(self):
        return ord(self.text)


class Space(Character):
    def __init__(self, style=DefaultStyle):
        Character.__init__(self, " ", style)


class Spacer(Space):
    def __init__(self, dimension):
        Space.__init__(self, " ", style=None)
        self.dimension = dimension

    def width(self):
        return float(dimension)


class Word(list):
    def __init__(self, characters=[]):
        list.__init__(self)
        for char in characters:
            self.append(self, char)

    def __repr__(self):
        text = ''
        for char in self:
            text += char.text

        return text

    def append(self, character):
        assert isinstance(character, Character)
        assert character.text not in (" ", "\t")
        list.append(self, character)

    def width(self):
        width = 0
        for i in range(len(self)):
            thisChar = self[i]
            width += thisChar.width()
            width += self.kerning(i)

        return width

    def kerning(self, index):
        kerning = 0.0
        if index != len(self) - 1:
            thisChar = self[index]
            nextChar = self[index+1]
            if thisChar.style == nextChar.style:
                typeface = thisChar.style.typeface
                font = typeface.font(thisChar.style.fontStyle)
                kern = font.psFont.metrics.kerning_pairs.get(
                    (thisChar.text, nextChar.text), 0.0)
                kerning = kern * float(thisChar.style.fontSize) / 1000.0

        return kerning


emStyle = TextStyle(name="emphasized", fontStyle=FontStyle.Italic)
boldStyle = TextStyle(name="bold", fontStyle=FontStyle.Bold)
italicStyle = TextStyle(name="italic", fontStyle=FontStyle.Italic)
boldItalicStyle = TextStyle(name="bold italic", fontStyle=FontStyle.BoldItalic)

class Bold(Text):
    def __init__(self, text):
        Text.__init__(self, text, style=boldStyle)

class Italic(Text):
    def __init__(self, text):
        Text.__init__(self, text, style=italicStyle)

class Em(Text):
    def __init__(self, text):
        Text.__init__(self, text, style=italicStyle)
