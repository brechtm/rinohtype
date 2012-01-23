
import re

from copy import copy
from html.entities import name2codepoint
from warnings import warn

from psg.fonts.encoding_tables import glyph_name_to_unicode

from .unit import pt
from .font.style import MEDIUM, UPRIGHT, NORMAL, BOLD, ITALIC
from .fonts import adobe14
from .warnings import PyteWarning
from .style import Style, Styled, ParentStyle, ParentStyleException


class TextStyle(Style):
    attributes = {'typeface': adobe14.times,
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


class CharacterLike(Styled):
    def __init__(self, style=ParentStyle):
        super().__init__(style)

    def __repr__(self):
        return "{0}(style={1})".format(self.__class__.__name__, self.style)

    @property
    def width(self):
        raise NotImplementedError

    @property
    def height(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError


# TODO: subclass str?
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

    def get_font(self):
        typeface = self.get_style('typeface')
        weight = self.get_style('fontWeight')
        slant = self.get_style('fontSlant')
        width = self.get_style('fontWidth')
        return typeface.get(weight=weight, slant=slant, width=width)

    def characters(self):
        for i, char in enumerate(self.text):
            try:
                character = special_chars[char]()
            except KeyError:
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
        super().__init__(text, style)
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
    def __init__(self, fixed_width=False, style=ParentStyle):
        super().__init__(' ', style)
        self.fixed_width = fixed_width

    def characters(self):
        yield self


class FixedWidthSpace(Space):
    def __init__(self, style=ParentStyle):
        super().__init__(True, style)


class NoBreakSpace(Character):
    def __init__(self, style=ParentStyle):
        super().__init__(' ', style)


class Spacer(FixedWidthSpace):
    def __init__(self, dimension):
        super().__init__(style=None)
        self.dimension = dimension

    @property
    def width(self):
        return float(self.dimension)


special_chars = {' ': Space,
                 chr(0xa0): NoBreakSpace}


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


class ControlCharacter(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.__class__.__name__

    def characters(self):
        yield self


class NewLine(ControlCharacter):
    def __init__(self):
        super().__init__('\n')


class Tab(ControlCharacter):
    def __init__(self):
        super().__init__('\t')


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
