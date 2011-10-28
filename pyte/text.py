
import re
import os

from copy import copy
from html.entities import name2codepoint
from warnings import warn

from psg.fonts.encoding_tables import glyph_name_to_unicode

from pyte.unit import pt
from pyte.font.style import MEDIUM, UPRIGHT, NORMAL, BOLD, ITALIC
from pyte.hyphenator import Hyphenator
from .warnings import PyteWarning


class ParentStyleException(Exception):
    pass


class ParentStyleType(type):
    def __getattr__(cls, key):
        raise ParentStyleException

    def __repr__(cls):
        return cls.__name__


class ParentStyle(object, metaclass=ParentStyleType):
    pass


class Style(object):
    attributes = {}

    def __init__(self, name, base=ParentStyle, **attributes):
        self.name = name
        self.base = base
        for attribute in attributes:
            if attribute not in self._supported_attributes():
                raise TypeError('%s is not a supported attribute' % attribute)
        self.__dict__.update(attributes)

    def __repr__(self):
        return '{0}({1}) > {2}'.format(self.__class__.__name__ , self.name,
                                       self.base)

        return self.get_default(name)

    def __getattr__(self, name):
        if self.base == None:
            return self._get_default(name)
        else:
            return getattr(self.base, name)

    def _get_default(self, name):
        for cls in self.__class__.__mro__:
            try:
                return cls.attributes[name]
            except (KeyError, AttributeError):
                pass
        raise AttributeError("No attribute '{}' in {}".format(name, self))

    def _supported_attributes(self):
        attributes = {}
        for cls in reversed(self.__class__.__mro__):
            try:
                attributes.update(cls.attributes)
            except AttributeError:
                pass
        return attributes


class TextStyle(Style):
    attributes = {'typeface': None, # no default fonts yet
                  'fontWeight': MEDIUM,
                  'fontSlant': UPRIGHT,
                  'fontWidth': NORMAL,
                  'fontSize': 10*pt, # TODO: change default
                  'smallCaps': False,
                  'hyphenate': True,
                  'hyphenChars': 2,
                  'hyphenLang': 'en'}

    def __init__(self, name, base=ParentStyle, **attributes):
        super().__init__(name, base=base, **attributes)

    def get_font(self):
        typeface = self.get('typeface')
        weight = self.get('fontWeight')
        slant = self.get('fontSlant')
        width = self.get('fontWidth')
        return typeface.get(weight=weight, slant=slant, width=width)


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
        self.cached_style = {}

    def __add__(self, other):
        assert isinstance(other, Styled) or isinstance(other, str)
        return MixedStyledText([self, other])

    def __radd__(self, other):
        assert isinstance(other, str)
        return MixedStyledText([other, self])

    def get_style(self, attribute):
        try:
            return self.cached_style[attribute]
        except KeyError:
            try:
                value = getattr(self.style, attribute)
            except ParentStyleException:
                value = self.parent.get_style(attribute)
            self.cached_style[attribute] = value
            return value

    def get_font(self):
        typeface = self.get_style('typeface')
        weight = self.get_style('fontWeight')
        slant = self.get_style('fontSlant')
        width = self.get_style('fontWidth')
        return typeface.get(weight=weight, slant=slant, width=width)

    def characters(self):
        raise NotImplementedError


class CharacterLike(Styled):
    def __init__(self, style=ParentStyle):
        super().__init__(style)

    def __repr__(self):
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.style)
    @property
    def width(self):
        raise NotImplementedError

    @property
    def height(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError


class StyledText(Styled):
    style_class = TextStyle

    def __init__(self, text, style=ParentStyle):
        super().__init__(style)
        text = self._clean_text(text)
        self.text = self._decode_html_entities(text)

    def _clean_text(self, text):
        text = re.sub('[\t\r\n]', ' ', text)
        return re.sub(' +', ' ', text)

    # from http://wiki.python.org/moin/EscapingHtml
    def _decode_html_entities(self, text):
        return re.sub('&(%s);' % '|'.join(name2codepoint),
                      lambda m: chr(name2codepoint[m.group(1)]), text)

    def __repr__(self):
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.text, self.style)

    def characters(self):
        for i, char in enumerate(self.text):
            character = Character(char, style=ParentStyle, new_span=(i==0))
            character.parent = self
            if self.get_style('smallCaps'):
                yield character.small_capital()
            else:
                yield character


class MixedStyledText(list, Styled):
    style_class = TextStyle

    def __init__(self, items, style=ParentStyle):
        Styled.__init__(self, style)
        if type(items) == str:
            items = [items]
        for item in items:
            if type(item) == str:
                item = StyledText(item, style=ParentStyle)
            item.parent = self
            self.append(item)

    def __repr__(self):
        return '{0} (style={1})'.format(super().__repr__(), self.style)

    def __add__(self, other):
##        assert (isinstance(other, MixedStyledText)
##                or isinstance(other, str))
        try:
            result = super().__add__(other)
        except TypeError:
            result = super().__add__([other])
        return __class__(result)

    def __iadd__(self, other):
        return self + other

    def __radd__(self, other):
##        assert isinstance(other, StyledText) \
##            or isinstance(other, MixedStyledText) \
##            or isinstance(other, str)
        return __class__(other) + self

    def characters(self):
        for item in self:
            for char in item.characters():
                yield char


# TODO: make following classes immutable (override setattr) and store widths
class Character(StyledText):
    def __init__(self, text, style=ParentStyle, new_span=False):
        #assert len(text) == 1
        super().__init__(text, style)
        if text in (' ', '\t'):
            self.__class__= Space
        elif text == chr(0x00a0): # no-break space
            self.__class__= NoBreakSpace
            self.text = ' '
        self.new_span = new_span

    def __repr__(self):
        return self.text

    @property
    def width(self):
        font = self.get_font()
        font_size = float(self.height)
        return font.psFont.metrics.stringwidth(self.text, font_size)

    @property
    def height(self):
        return self.get_style('fontSize')

    @property
    def glyph_name(self):
        ps_font = self.get_font().psFont
        try:
            return ps_font.metrics[self.ord()].ps_name
        except KeyError:
            warn("{0} does not contain glyph for unicode index 0x{1:04x} ({2})"
                 .format(ps_font.ps_name, self.ord(), self.text), PyteWarning)
            return ps_font.metrics[ord('?')].ps_name

    def ord(self):
        return ord(self.text)

    sc_suffixes = ('.smcp', '.sc', 'small')

    def small_capital(self):
        ps_font = self.get_font().psFont
        char = self.text
        for suffix in self.sc_suffixes:
            if ps_font.has_glyph(char + suffix):
                glyph = Glyph(char + '.sc')
            elif char.islower() and ps_font.has_glyph(char.upper() + suffix):
                glyph = Glyph(char.upper() + '.sc')
        try:
            glyph.parent = self.parent
            return glyph
        except NameError:
            warn('{} does not contain small capitals for one or more '
                 'characters'.format(self.get_font().psFont.ps_name),
                 PyteWarning)
            return self

    def kerning(self, next_character):
        if self.style != next_character.style:
            #TODO: fine-grained style compare?
            raise TypeError

        font_metrics = self.get_font().psFont.metrics
        return font_metrics.get_kerning(self.glyph_name,
                                        next_character.glyph_name)

    def ligature(self, next_character):
        if self.style != next_character.style:
            #TODO: fine-grained style compare?
            raise TypeError

        font_metrics = self.get_font().psFont.metrics.FontMetrics
        char_metrics = font_metrics["Direction"][0]["CharMetrics"]
        try:
            ligatures = char_metrics.by_glyph_name[self.glyph_name]['L']
            lig_glyph_name = ligatures[next_character.glyph_name]
            lig_text = self.text + next_character.text
            ligature = Glyph(lig_glyph_name, lig_text, style=self.style)
            ligature.parent = self.parent
            return ligature
        except KeyError:
            raise TypeError


class Glyph(Character):
    def __init__(self, name, text='?', style=ParentStyle):
        super().__init__(text, style)
        self.name = name

    def __repr__(self):
        return "<glyph '{0}'> (style={1})".format(self.name, self.style)

    @property
    def width(self):
        font = self.get_font()
        font_size = float(self.get_style('fontSize'))
        return font.psFont.metrics.stringwidth([self.name], font_size)

    @property
    def glyph_name(self):
        return self.name

    def ord(self):
        raise TypeError


class Space(Character):
    def __init__(self, style=ParentStyle):
        super().__init__(' ', style)
        self.text = ' '


class Spacer(Space):
    def __init__(self, dimension):
        super().__init__(style=None)
        self.dimension = dimension

    def width(self):
        return float(dimension)


class NoBreakSpace(Space):
    pass


# TODO: shared superclass SpecialChar (or ControlChar) for Newline, Box, Tab
class Box(Character):
    def __init__(self, width, height, depth, ps):
        super().__init__('?', new_span=True)
        self._width = width
        self._height = height
        self.depth = depth
        self.ps = ps

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def kerning(self, next_character):
        raise TypeError

    def ligature(self, next_character):
        raise TypeError


# TODO: refactor to LineBreak
class NewLine(Character):
    def __init__(self, style=ParentStyle):
        super().__init__('\n', style)

    def kerning(self, next_character):
        raise TypeError

    def ligature(self, next_character):
        raise TypeError


class Tab(Character):
    def __init__(self, style=ParentStyle):
        super().__init__('\t', style)


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

    stringwidth = None
    font_size = None

    def __repr__(self):
        return ''.join([char.text for char in self])

    def __getitem__(self, index):
        result = super().__getitem__(index)
        if type(index) == slice:
            result = __class__(result)
        return result

    def append(self, char):
        if isinstance(char, Character):
            if self.hyphen_enable:
                self.hyphen_enable = char.get_style('hyphenate')
                self.hyphen_chars = max(self.hyphen_chars,
                                        char.get_style('hyphenChars'))
                if self.hyphen_lang is None:
                    self.hyphen_lang = char.get_style('hyphenLang')
                elif char.get_style('hyphenLang') != self.hyphen_lang:
                    self.hyphen_enable = False
        elif isinstance(char, Box):
            # TODO: should a Box even be a part of a Word?
            pass
        else:
            raise ValueError('expecting Character or Box')
        super().append(char)

    def substitute_ligatures(self):
        i = 0
        while i + 1 < len(self):
            character = self[i]
            next_character = self[i + 1]
            try:
                self[i] = character.ligature(next_character)
                del self[i + 1]
            except TypeError:
                i += 1

    def width(self, kerning=True):
        width = 0.0
        for i, character in enumerate(self):
            if isinstance(character, Box):
                width += character.width
            else:
                if self.stringwidth is None or character.new_span:
                    self.font_metrics = character.get_font().psFont.metrics
                    self.stringwidth = self.font_metrics.stringwidth
                    self.font_size = float(character.get_style('fontSize'))

                width += self.stringwidth(character.text, self.font_size)
                if kerning:
                    width += self.kerning(i)
        return width

    def kerning(self, index):
        if index == len(self) - 1:
            kerning = 0.0
        else:
            this_char = self[index]
            next_char = self[index + 1]
            try:
                kern = this_char.kerning(next_char)
                kerning = kern * float(self.font_size) / 1000.0
            except TypeError:
                kerning = 0.0

        return kerning

    dic_dir = os.path.join(os.path.dirname(__file__), 'data', 'hyphen')

    def hyphenate(self):
        if not self.hyphen_enable:
            return

        dic_path = dic_file = 'hyph_{}.dic'.format(self.hyphen_lang)
        if not os.path.exists(dic_path):
            dic_path = os.path.join(self.dic_dir, dic_file)
            if not os.path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))

        word = str(self)
        h = Hyphenator(dic_path, self.hyphen_chars, self.hyphen_chars)
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

emStyle = TextStyle(name="emphasized", fontSlant=ITALIC)
boldStyle = TextStyle(name="bold", fontWeight=BOLD)
italicStyle = TextStyle(name="italic", fontSlant=ITALIC)
boldItalicStyle = TextStyle(name="bold italic", fontWeight=BOLD,
                            fontSlant=ITALIC)
smallCapsStyle = TextStyle(name="small capitals", smallCaps=True)


class Bold(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=boldStyle)


class Italic(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=italicStyle)


class Emphasized(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=italicStyle)


class SmallCaps(StyledText):
    def __init__(self, text):
        StyledText.__init__(self, text, style=smallCapsStyle)
