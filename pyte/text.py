
import itertools
import re
import os

from copy import copy
from html.entities import name2codepoint
from warnings import warn

from psg.fonts.encoding_tables import glyph_name_to_unicode

from .hyphenator import Hyphenator
from .unit import pt
from .font.style import MEDIUM, UPRIGHT, NORMAL, BOLD, ITALIC
from .font.style import SUPERSCRIPT, SUBSCRIPT
from .fonts import adobe14
from .warnings import PyteWarning
from .style import Style, Styled, ParentStyle, ParentStyleException
from .util import cached_property


class TextStyle(Style):
    attributes = {'typeface': adobe14.times,
                  'fontWeight': MEDIUM,
                  'fontSlant': UPRIGHT,
                  'fontWidth': NORMAL,
                  'fontSize': 10*pt, # TODO: change default
                  'smallCaps': False,
                  'position': NORMAL,
                  'kerning': True,
                  'ligatures': True,
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

    def __init__(self, text, style=ParentStyle, y_offset=0):
        super().__init__(style)
        text = self._clean_text(text)
        self.text = self._decode_html_entities(text)
        self.y_offset = y_offset

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

    def __getitem__(self, index):
        result = self.__class__(self.text[index])
        result.parent = self.parent
        return result

    def split(self):
        def is_special(char):
            return char in special_chars.keys()

        for special, lst in itertools.groupby(self.text, is_special):
            if special:
                for char in lst:
                    item = special_chars[char](y_offset=self.y_offset)
                    item.parent = self
                    yield item
            else:
                item = self.__class__(''.join(lst), y_offset=self.y_offset)
                item.parent = self
                yield item

    def get_font(self):
        typeface = self.get_style('typeface')
        weight = self.get_style('fontWeight')
        slant = self.get_style('fontSlant')
        width = self.get_style('fontWidth')
        return typeface.get(weight=weight, slant=slant, width=width)

    @cached_property
    def ps_font(self):
        return self.get_font().psFont

    @property
    def height(self):
        return self.get_style('fontSize')

    @property
    def width(self):
        return sum(self.widths)

    @cached_property
    def widths(self):
        font_size = float(self.height) / 1000.0
        font_metrics = self.get_font().psFont.metrics
        char_metrics = font_metrics.FontMetrics["Direction"][0]["CharMetrics"].by_glyph_name
        kerning = self.get_style('kerning')
        glyphs = self.glyphs()
        widths = []

        prev_glyph = next(glyphs)
        prev_width = char_metrics[prev_glyph]['W0X']
        for glyph in glyphs:
            if kerning:
                prev_width += font_metrics.get_kerning(prev_glyph, glyph)
            widths.append(prev_width * font_size)
            prev_width = char_metrics[glyph]['W0X']
            prev_glyph = glyph
        widths.append(prev_width * font_size)
        return widths

    def char_to_glyph(self, character):
        font_metrics = self.ps_font.metrics
        try:
            return font_metrics[ord(character)].ps_name
        except KeyError:
            warn('{} does not contain glyph for unicode index 0x{:04x} ({})'
                 .format(self.ps_font.ps_name, ord(character), character),
                 PyteWarning)
            return font_metrics[ord('?')].ps_name

    def glyphs(self):
        font_metrics = self.ps_font.metrics
        char_metrics = font_metrics.FontMetrics["Direction"][0]["CharMetrics"].by_glyph_name
        characters = iter(self.text)

        prev_char = self.text[0]
        prev_glyph = self.char_to_glyph(next(characters))
        for char in characters:
            glyph = self.char_to_glyph(char)
            try:
                prev_glyph = char_metrics[prev_glyph]['L'][glyph]
                prev_char = prev_char + char
            except KeyError:
                yield prev_glyph
                prev_glyph = glyph
        yield prev_glyph

    dic_dir = os.path.join(os.path.dirname(__file__), 'data', 'hyphen')

    @property
    def _hyphenator(self):
        hyphen_lang = self.get_style('hyphenLang')
        hyphen_chars = self.get_style('hyphenChars')
        dic_path = dic_file = 'hyph_{}.dic'.format(hyphen_lang)
        if not os.path.exists(dic_path):
            dic_path = os.path.join(self.dic_dir, dic_file)
            if not os.path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))
        return Hyphenator(dic_path, hyphen_chars, hyphen_chars)

    def hyphenate(self):
        if self.get_style('hyphenate'):
            word = self.text
            h = self._hyphenator
            for position in reversed(h.positions(word)):
                parts = h.wrap(word, position + 1)
                if ''.join((parts[0][:-1], parts[1])) != word:
                    raise NotImplementedError
                first, second = self[:position], self[position:]
                first.text += '-'
                yield first, second

    superscript_position = 1 / 3
    subscript_position = - 1 / 6
    position_size = 583 / 1000

    def spans(self):
        span = self
        if self.get_style('position') == SUPERSCRIPT:
            offset = float(self.height) * self.superscript_position
            size = float(self.height) * self.position_size
            style = TextStyle(name='super', position=NORMAL, fontSize=size)
            span = StyledText(self.text, style, y_offset=offset)
            span.parent = self.parent
        elif self.get_style('position') == SUBSCRIPT:
            offset = float(self.height) * self.subscript_position
            size = float(self.height) * self.position_size
            style = TextStyle(name='sub', position=NORMAL, fontSize=size)
            span = StyledText(self.text, style, y_offset=offset)
            span.parent = self.parent
        if self.get_style('smallCaps'):
            span = SmallCapitalsText(span.text, span.style,
                                     y_offset=self.y_offset)
            span.parent = self.parent
            yield span
        else:
            yield span


class SmallCapitalsText(StyledText):
    def __init__(self, text, style=ParentStyle, y_offset=0):
        super().__init__(text, style, y_offset=y_offset)

    suffixes = ('.smcp', '.sc', 'small')

    def _find_suffix(self, glyph, upper=False):
        has_glyph = self.ps_font.has_glyph
        for suffix in self.suffixes:
            if has_glyph(glyph + suffix):
                self.get_font().sc_sufix = suffix
                return True
        if not upper:
            return self._find_suffix(glyph.upper(), True)
        return False

    def char_to_glyph(self, char):
        glyph = super().char_to_glyph(char)
        font = self.get_font()
        has_glyph = font.psFont.has_glyph
        try:
            if has_glyph(glyph + font.sc_sufix):
                sc_glyph = glyph + font.sc_sufix
        except AttributeError:
            if self._find_suffix(glyph):
                sc_glyph = glyph + font.sc_sufix
        try:
            return sc_glyph
        except NameError:
            warn('{} does not contain small capitals for one or more characters'
                 .format(font.psFont.ps_name), PyteWarning)
            return glyph


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
        return '{}{} (style={})'.format(self.__class__.__name__,
                                        super().__repr__(), self.style)

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

    def spans(self):
        # TODO: support for mixed-style words
        # TODO: kerning between Glyphs
        for item in self:
            for span in item.spans():
                yield span


# TODO: make following classes immutable (override setattr) and store widths
class Character(StyledText):
    def __init__(self, text, style=ParentStyle, y_offset=0):
        super().__init__(text, style, y_offset=y_offset)

    def __repr__(self):
        return self.text

    def split(self):
        yield self


class Glyph(Character):
    def __init__(self, name, text='?', style=ParentStyle):
        super().__init__(text, style)
        self.name = name

    def __repr__(self):
        return "<glyph '{0}'> (style={1})".format(self.name, self.style)

    def glyphs(self):
        yield self.name


class Space(Character):
    def __init__(self, fixed_width=False, style=ParentStyle, y_offset=0):
        super().__init__(' ', style, y_offset=y_offset)
        self.fixed_width = fixed_width


class FixedWidthSpace(Space):
    def __init__(self, style=ParentStyle):
        super().__init__(True, style)


class NoBreakSpace(Character):
    def __init__(self, style=ParentStyle, y_offset=0):
        super().__init__(' ', style, y_offset=y_offset)


class Spacer(FixedWidthSpace):
    def __init__(self, dimension):
        super().__init__(style=None)
        self.dimension = dimension

    @property
    def widths(self):
        yield float(self.dimension)


special_chars = {' ': Space,
                 chr(0xa0): NoBreakSpace}


# TODO: shared superclass SpecialChar (or ControlChar) for Newline, Box, Tab
class Box(Character):
    def __init__(self, width, height, depth, ps):
        super().__init__('?')
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

    def render(self, canvas, x, y):
        box_canvas = canvas.append_new(x, y - self.depth, self.width,
                                       self.height + self.depth)
        print(self.ps, file=box_canvas.psg_canvas)
        return self.width


class ControlCharacter(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.__class__.__name__


class NewLine(ControlCharacter):
    def __init__(self):
        super().__init__('\n')


class Tab(ControlCharacter, Character):
    def __init__(self):
        Character.__init__(self, ' ')
        super().__init__(' ')
        self.tab_width = 0


class FlowableEmbedder(object):
    def __init__(self, flowable):
        self.flowable = flowable

    def spans(self):
        self.flowable.parent = self.parent
        yield self.flowable


# predefined styles

emStyle = TextStyle(name="emphasized", fontSlant=ITALIC)
boldStyle = TextStyle(name="bold", fontWeight=BOLD)
italicStyle = TextStyle(name="italic", fontSlant=ITALIC)
boldItalicStyle = TextStyle(name="bold italic", fontWeight=BOLD,
                            fontSlant=ITALIC)
smallCapsStyle = TextStyle(name="small capitals", smallCaps=True)
superscriptStyle = TextStyle(name="superscript", position=SUPERSCRIPT)
subscriptStyle = TextStyle(name="subscript", position=SUBSCRIPT)


class Bold(StyledText):
    def __init__(self, text, y_offset=0):
        StyledText.__init__(self, text, style=boldStyle, y_offset=y_offset)


class Italic(StyledText):
    def __init__(self, text, y_offset=0):
        StyledText.__init__(self, text, style=italicStyle, y_offset=y_offset)


class Emphasized(StyledText):
    def __init__(self, text, y_offset=0):
        StyledText.__init__(self, text, style=italicStyle, y_offset=y_offset)


class SmallCaps(StyledText):
    def __init__(self, text, y_offset=0):
        StyledText.__init__(self, text, style=smallCapsStyle, y_offset=y_offset)


class Superscript(StyledText):
    def __init__(self, text, y_offset=0):
        StyledText.__init__(self, text, style=superscriptStyle, y_offset=y_offset)


class Subscript(StyledText):
    def __init__(self, text, y_offset=0):
        StyledText.__init__(self, text, style=subscriptStyle, y_offset=y_offset)
