
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
from .font.style import SMALL_CAPITAL
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
                  'hyphenLang': 'en_US'}

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


class StyledText(Styled):
    style_class = TextStyle

    def __init__(self, style=ParentStyle, y_offset=0):
        super().__init__(style)
        self._y_offset = y_offset

    def __add__(self, other):
        assert isinstance(other, __class__) or isinstance(other, str)
        return MixedStyledText([self, other])

    def __radd__(self, other):
        assert isinstance(other, str)
        return MixedStyledText([other, self])

    def __iadd__(self, other):
        return self + other

    superscript_position = 1 / 3
    subscript_position = - 1 / 6
    position_size = 583 / 1000

    @property
    def height(self):
        height = float(self.get_style('fontSize'))
        if self.get_style('position') in (SUPERSCRIPT, SUBSCRIPT):
            height *= self.position_size
        return height

    @property
    def y_offset(self):
        try:
            offset = self.parent.y_offset + self._y_offset
        except (TypeError, AttributeError):
            offset = self._y_offset
        try:
            # The Y offset should only change once for the nesting level where
            # the position style is set, hence we don't recursively get the
            # position style
            if self.style.position == SUPERSCRIPT:
                offset += float(self.get_style('fontSize')) * self.superscript_position
            elif self.style.position == SUBSCRIPT:
                offset += float(self.get_style('fontSize')) * self.subscript_position
        except ParentStyleException:
            pass
        return offset


# TODO: subclass str (requires messing around with __new__)?
class SingleStyledText(StyledText):
    def __init__(self, text, style=ParentStyle, y_offset=0):
        super().__init__(style, y_offset)
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
                    item = special_chars[char]()
                    item.parent = self
                    yield item
            else:
                item = self.__class__(''.join(lst))
                item.parent = self
                yield item

    @cached_property
    def font(self):
        typeface = self.get_style('typeface')
        weight = self.get_style('fontWeight')
        slant = self.get_style('fontSlant')
        width = self.get_style('fontWidth')
        return typeface.get(weight=weight, slant=slant, width=width)

    @property
    def width(self):
        return sum(self.widths)

    @cached_property
    def widths(self):
        scale = float(self.height) / self.font.scaling_factor
        get_kerning = self.font.metrics.get_kerning
        kerning = self.get_style('kerning')
        glyphs = self.glyphs()
        widths = []

        prev_glyph = next(glyphs)
        prev_width = prev_glyph.width
        for glyph in glyphs:
            if kerning:
                prev_width += get_kerning(prev_glyph, glyph)
            widths.append(prev_width * scale)
            prev_width = glyph.width
            prev_glyph = glyph
        widths.append(prev_width * scale)
        return widths

    def glyphs(self, variant=None):
        characters = iter(self.text)
        get_glyph = lambda char: self.font.metrics.get_glyph(char, variant)
        prev_glyph = get_glyph(next(characters))
        for char in characters:
            glyph = get_glyph(char)
            ligature = self.font.metrics.get_ligature(prev_glyph, glyph)
            if ligature:
                prev_glyph = ligature
            else:
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

    def spans(self):
        span = self
        if self.get_style('smallCaps'):
            span = SmallCapitalsText(span.text, span.style,
                                     y_offset=self.y_offset)
            span.parent = self.parent
        yield span


class SmallCapitalsText(SingleStyledText):
    def __init__(self, text, style=ParentStyle, y_offset=0):
        super().__init__(text, style, y_offset=y_offset)

    def glyphs(self):
        return super().glyphs(SMALL_CAPITAL)


class MixedStyledText(StyledText, list):
    style_class = TextStyle

    def __init__(self, items, style=ParentStyle, y_offset=0):
        StyledText.__init__(self, style, y_offset)
        # TODO: handle y_offset
        if isinstance(items, str):
            items = [items]
        for item in items:
            if isinstance(item, str):
                item = SingleStyledText(item, style=ParentStyle)
            item.parent = self
            self.append(item)

    def __repr__(self):
        return '{}{} (style={})'.format(self.__class__.__name__,
                                        super().__repr__(), self.style)

    def spans(self):
        # TODO: support for mixed-style words
        # TODO: kerning between Glyphs
        for item in self:
            for span in item.spans():
                yield span


# TODO: make following classes immutable (override setattr) and store widths
class Character(SingleStyledText):
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
        box_canvas = canvas.new(x, y - self.depth, self.width,
                                self.height + self.depth)
        print(self.ps, file=box_canvas.psg_canvas)
        canvas.append(box_canvas)
        return self.width


class ControlCharacter(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.__class__.__name__

    def split(self):
        yield self

    def spans(self):
        yield self


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


class Bold(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=boldStyle, y_offset=y_offset)


class Italic(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=italicStyle, y_offset=y_offset)


class Emphasized(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=italicStyle, y_offset=y_offset)


class SmallCaps(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=smallCapsStyle, y_offset=y_offset)


class Superscript(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=superscriptStyle, y_offset=y_offset)


class Subscript(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=subscriptStyle, y_offset=y_offset)
