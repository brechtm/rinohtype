
import re
from copy import copy
from html.entities import name2codepoint

from psg.fonts.encoding_tables import glyph_name_to_unicode

from pyte.unit import pt
from pyte.font import TypeFace, FontStyle
from pyte.hyphenator import Hyphenator


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

    def get_font(self):
        return self.get_style('typeface').font(self.get_style('fontStyle'))

    def characters(self):
        raise NotImplementedError


class StyledText(Styled):
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
        assert isinstance(other, StyledText) or isinstance(other, str)
        return MixedStyledText((self, other))

    def __radd__(self, other):
        assert isinstance(other, str)
        return MixedStyledText((other, self))

    def characters(self):
        for char in self.text:
            character = Character(char, style=ParentStyle)
            character.parent = self
            if self.get_style('smallCaps'):
                yield character.small_capital()
            else:
                yield character


class MixedStyledText(tuple, Styled):
    def __new__(cls, items, style=ParentStyle):
        if type(items) == str:
            items = (items, )
        texts = []
        for item in items:
            if type(item) == str:
                item = StyledText(item, style=ParentStyle)
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
##        assert isinstance(other, StyledText) \
##            or isinstance(other, MixedStyledText) \
##            or isinstance(other, str)
        result = self.__class__(other) + self
        return self.__class__(result)

    def characters(self):
        for item in self:
            for char in item.characters():
                yield char


# TODO: make following classes immutable (override setattr) and store widths
class Character(StyledText):
    def __init__(self, text, style=ParentStyle):
        assert len(text) == 1
        super().__init__(text, style)
        if text in (' ', '\t'):
            self.__class__= Space

    def width(self):
        font = self.get_font()
        font_size = float(self.get_style('fontSize'))
        return font.psFont.metrics.stringwidth(self.text, font_size)

    def ord(self):
        return ord(self.text)

    sc_suffixes = ('.smcp', '.sc', 'small')

    def small_capital(self):
        font = self.get_font()
        char = self.text
        for suffix in self.sc_suffixes:
            if font.psFont.has_char(char + suffix):
                glyph = Glyph(char + '.sc')
            elif char.islower() and font.psFont.has_char(char.upper() + suffix):
                glyph = Glyph(char.upper() + '.sc')
        try:
            glyph.parent = self.parent
            return glyph
        except NameError:
            return self


class Glyph(Character):
    def __init__(self, name, style=ParentStyle):
        super().__init__('?', style)
        self.name = name

    def __repr__(self):
        return "<glyph '{0}'> (style={1})".format(self.name, self.style)

    def _ps_repr(self):
        try:
            ps_repr = glyph_name_to_unicode[self.name]
        except KeyError:
            ps_repr = self.name
        return ps_repr

    def width(self):
        font = self.get_font()
        font_size = float(self.get_style('fontSize'))
        return font.psFont.metrics.stringwidth([self._ps_repr()], font_size)

    def ord(self):
        return self._ps_repr()


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
        self.hyphen_enable = True
        self.hyphen_chars = 0
        self.hyphen_lang = None
        for char in characters:
            self.append(char)

    def __repr__(self):
        return ''.join([char.text for char in self])

    def __getitem__(self, index):
        result = super().__getitem__(index)
        if type(index) == slice:
            result = __class__(result)
        return result

    def append(self, char):
        assert isinstance(char, Character)
        assert char.text not in (" ", "\t")
        if self.hyphen_enable:
            self.hyphen_enable = char.get_style('hyphenate')
            self.hyphen_chars = max(self.hyphen_chars,
                                    char.get_style('hyphenChars'))
            if self.hyphen_lang is None:
                self.hyphen_lang = char.get_style('hyphenLang')
            elif char.get_style('hyphenLang') != self.hyphen_lang:
                self.hyphen_enable = False
        super().append(char)

    def substitute_ligatures(self):
        ligatured = __class__()
        previous = self[0]
        for character in self[1:]:
            font_metrics = character.get_font().psFont.metrics
            char_metrics = font_metrics.FontMetrics["Direction"][0]["CharMetrics"]
            try:
                # TODO: verify whether styles are identical
                ligatures = char_metrics[previous.ord()]['L']
                # TODO: check for other standard ligatures (ij)

                ligature_glyph_name = ligatures[character.text]
                previous = Glyph(ligature_glyph_name)
                previous.parent = character.parent
            except KeyError:
                ligatured.append(previous)
                previous = character

        ligatured.append(previous)
        return ligatured

    def width(self, kerning=True):
        width = 0.0
        for i, character in enumerate(self):
            width += character.width()
            if kerning:
                width += self.kerning(i)
        return width

    def kerning(self, index):
        if index == len(self) - 1:
            kerning = 0.0
        else:
            this = self[index]
            next = self[index+1]
            # FIXME: different styles can have the same font/size/weight
            if this.style == next.style:
                font = this.get_font()
                kp = font.psFont.metrics.kerning_pairs
                kern = font.psFont.metrics.kerning_pairs.get(
                    (this.ord(), next.ord()), 0.0)
                kerning = kern * float(this.get_style('fontSize'))/ 1000.0

        return kerning

    def hyphenate(self):
        if not self.hyphen_enable:
            return
        word = str(self)
        h = Hyphenator('hyph_{}.dic'.format(self.hyphen_lang),
                       left=self.hyphen_chars, right=self.hyphen_chars)
        for position in reversed(h.positions(word)):
            parts = h.wrap(word, position + 1)
            if "".join((parts[0][:-1], parts[1])) != word:
                raise NotImplementedError
            first, second = self[:position], self[position:]
            hyphen = Character('-', style=first[-1].style)
            hyphen.parent = first[-1].parent
            first.append(hyphen)
            yield first, second


# predefined styles

emStyle = TextStyle(name="emphasized", fontStyle=FontStyle.Italic)
boldStyle = TextStyle(name="bold", fontStyle=FontStyle.Bold)
italicStyle = TextStyle(name="italic", fontStyle=FontStyle.Italic)
boldItalicStyle = TextStyle(name="bold italic", fontStyle=FontStyle.BoldItalic)
smallCapsStyle = TextStyle(name="small capitals", smallCaps=True)


class Bold(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=boldStyle)


class Italic(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=italicStyle)


class Em(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=italicStyle)


class SmallCaps(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=smallCapsStyle)
