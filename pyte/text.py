
import re
from html.entities import name2codepoint

from pyte.unit import pt
from pyte.font import TypeFace, FontStyle


class ParentStyleException(Exception):
    pass


class ParentStyleType(type):
    def __getattr__(cls, key):
        raise ParentStyleException

    def __repr__(cls):
        return cls.__name__


class ParentStyle(object, metaclass=ParentStyleType):
    pass


class TextStyle(object):
    attributes = {'typeface': None, # no default fonts yet
                  'fontStyle': FontStyle.Roman,
                  'fontSize': 10*pt, # TODO: change default
                  'smallCaps': False,
                  'hyphenate': True,
                  'hyphenChars': 2,
                  'hyphenLang': 'en'}

    def _get_default(self, name):
        for cls in self.__class__.__mro__:
            try:
                return cls.attributes[name]
            except (KeyError, AttributeError):
                pass
        raise AttributeError

    def _supported_attributes(self):
        attributes = {}
        for cls in reversed(self.__class__.__mro__):
            try:
                attributes.update(cls.attributes)
            except AttributeError:
                pass
        return attributes

    def __init__(self, name, base=ParentStyle, **attributes):
        self.name = name
        self.base = base
        for attribute in attributes:
            if attribute not in self._supported_attributes():
                raise TypeError('%s is not a supported attribute' % attribute)
        self.__dict__.update(attributes)

    def __getattr__(self, name):
        if self.base == None:
            return self._get_default(name)
        else:
            return getattr(self.base, name)

    def __repr__(self):
        return '{0}({1}) > {2}'.format(self.__class__.__name__ , self.name,
                                       self.base)

        return self.get_default(name)


emStyle = TextStyle(name="emphasized", fontStyle=FontStyle.Italic)
boldStyle = TextStyle(name="bold", fontStyle=FontStyle.Bold)
italicStyle = TextStyle(name="italic", fontStyle=FontStyle.Italic)
boldItalicStyle = TextStyle(name="bold italic", fontStyle=FontStyle.BoldItalic)
parentStyle = TextStyle(name="parent")


# TODO: link to xml line number
class Styled(object):
    style_class = None

    def __init__(self, style=None):
        if style is None:
            style = self.style_class('empty')
        if style != ParentStyle and not isinstance(style, self.style_class):
            raise TypeError('the style passed to {0} should be of type {1}'
                            .format(self.__class__.__name__,
                                    self.style_class.__name__))
        self.style = style
        self.parent = None

    def get_style(self, attribute):
        try:
            return getattr(self.style, attribute)
        except ParentStyleException:
            return self.parent.get_style(attribute)

    def characters(self):
        raise NotImplementedError


class Text(Styled):
    style_class = TextStyle

    def __init__(self, text, style=ParentStyle):
        super().__init__(style)
        self.text = self._decode_html_entities(text)

    # from http://wiki.python.org/moin/EscapingHtml
    def _decode_html_entities(self, text):
        return re.sub('&(%s);' % '|'.join(name2codepoint),
                      lambda m: chr(name2codepoint[m.group(1)]), text)

    def __repr__(self):
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.text, self.style)

    def __add__(self, other):
        assert isinstance(other, Text) or isinstance(other, str)
        return MixedStyledText((self, other))

    def __radd__(self, other):
        assert isinstance(other, str)
        return MixedStyledText((other, self))

    def characters(self):
        for char in self.text:
            character = Character(char, style=ParentStyle)
            character.parent = self
            yield character


class MixedStyledText(tuple, Styled):
    def __new__(cls, items, style=ParentStyle):
        if type(items) == str:
            items = (items, )
        texts = []
        for item in items:
            if type(item) == str:
                item = Text(item, style=ParentStyle)
            texts.append(item)

        obj = tuple.__new__(cls, texts)
        for item in obj:
            item.parent = obj
        return obj

    def __init__(self, items, style=ParentStyle):
        Styled.__init__(self, style)

    def __repr__(self):
        return '{0} (style={1})'.format(super().__repr__(), self.style)

    def __add__(self, other):
##        assert (isinstance(other, MixedStyledText)
##                or isinstance(other, str))
        try:
            result = super().__add__(other)
        except TypeError:
            result = super().__add__((other, ))
        return self.__class__(result)

    def __radd__(self, other):
##        assert isinstance(other, Text) \
##            or isinstance(other, MixedStyledText) \
##            or isinstance(other, str)
        result = self.__class__(other) + self
        return self.__class__(result)

    def characters(self):
        for item in self:
            for char in item.characters():
                yield char


# TODO: make following classes immutable (override setattr) and store widths
class Character(Text):
    def __init__(self, text, style=ParentStyle):
        assert len(text) == 1
        super().__init__(text, style)
        if text in (' ', '\t'):
            self.__class__= Space

    def width(self):
        typeface = self.get_style('typeface')
        font_size = float(self.get_style('fontSize'))
        font = typeface.font(self.get_style('fontStyle'))
        return font.psFont.metrics.stringwidth(self.text, font_size)

    def ord(self):
        return ord(self.text)

    def characters(self):
        yield self


class Glyph(Character):
    def __init__(self, name, style=ParentStyle):
        super().__init__('?', style)
        self.name = name

    def __repr__(self):
        return "<glyph '{0}'> (style={1})".format(self.name, self.style)

    def width(self):
        typeface = self.get_style('typeface')
        font_size = float(self.get_style('fontSize'))
        font = typeface.font(self.get_style('fontStyle'))
        return font.psFont.metrics.stringwidth([self.name], font_size)

    def ord(self):
        return self.name


class Space(Character):
    def __init__(self, style=ParentStyle):
        super().__init__(' ', style)


class Spacer(Space):
    def __init__(self, dimension):
        super().__init__(style=None)
        self.dimension = dimension

    def width(self):
        return float(dimension)


class Word(list):
    def __init__(self, characters=None):
        if characters == None:
            characters = []
        super().__init__()
        for char in characters:
            self.append(self, char)

    def __repr__(self):
        return ''.join([char.text for char in self])

    def append(self, character):
        assert isinstance(character, Character)
        assert character.text not in (" ", "\t")
        super().append(character)

    def width(self):
        width = 0.0
        for i in range(len(self)):
            thisChar = self[i]
            #print(thisChar, thisChar.parent)
            width += thisChar.width()
            width += self.kerning(i)

        return width

    def kerning(self, index):
        kerning = 0.0
        if index != len(self) - 1:
            thisChar = self[index]
            nextChar = self[index+1]
            if thisChar.style == nextChar.style:
                typeface = thisChar.get_style('typeface')
                font = typeface.font(thisChar.get_style('fontStyle'))
                kern = font.psFont.metrics.kerning_pairs.get(
                    (thisChar.text, nextChar.text), 0.0)
                kerning = kern * float(thisChar.get_style('fontSize'))/ 1000.0

        return kerning


class Bold(Text):
    def __init__(self, text):
        Text.__init__(self, text, style=boldStyle)


class Italic(Text):
    def __init__(self, text):
        Text.__init__(self, text, style=italicStyle)


class Em(Text):
    def __init__(self, text):
        Text.__init__(self, text, style=italicStyle)


def SmallCaps(text):
    return text
    upped = []
    for char in text:
        # FIXME: use parent style instead of default style
        typeface = TextStyle.default.typeface
        font = typeface.font(TextStyle.default.fontStyle)
        if font.psFont.has_char(char + '.sc'):
            char = Glyph(char + '.sc', style=parentStyle)
        upped.append(char)
    return StyledText(upped)
