
import itertools
import os
import re

from .hyphenator import Hyphenator
from .dimension import PT
from .font.style import MEDIUM, UPRIGHT, NORMAL, BOLD, ITALIC
from .font.style import SUPERSCRIPT, SUBSCRIPT
from .font.style import SMALL_CAPITAL
from .fonts import adobe14
from .style import Style, Styled, PARENT_STYLE, ParentStyleException
from .util import intersperse, cached_property


__all__ = ['TextStyle', 'SingleStyledText', 'MixedStyledText']


class TextStyle(Style):
    """The :class:`Style` for :class:`StyledText` objects. It has the following
    attributes:

    * `typeface`: :class:`TypeFace` to set the text in.
    * `font_weight`: Thickness of the character outlines relative to their
                     height.
    * `font_slant`: Slope of the characters.
    * `font_width`: Stretch of the characters.
    * `font_size`: Height of characters expressed in PostScript points or
                   :class:`Dimension`.
    * `small_caps`: Use small capital glyphs or not (:class:`bool`).
    * `position`: Vertical text position; normal, super- or subscript.
    * `kerning`: Improve inter-letter spacing (:class:`bool`).
    * `ligatures`: Run letters together, where possible (:class:`bool`).
    * `hyphenate`: Allow words to be broken over two lines (:class:`bool`).
    * `hyphen_chars`: Minimum number of characters in either part of a
                      hyphenated word (:class:`int`).
    * `hyphen_lang`: Language to use for hyphenation. Accepts language locale
                     codes, such as 'en_US' (:class:`str`).

    `font_weight`, `font_slant`, `font_width` and `position` accept the values
    defined in the :mod:`font.style` module.

    The default value for each of the style attributes are defined in the
    :attr:`attributes` attribute."""

    attributes = {'typeface': adobe14.times,
                  'font_weight': MEDIUM,
                  'font_slant': UPRIGHT,
                  'font_width': NORMAL,
                  'font_size': 10*PT,
                  'small_caps': False,
                  'position': None,
                  'kerning': True,
                  'ligatures': True,
                  'hyphenate': True,
                  'hyphen_chars': 2,
                  'hyphen_lang': 'en_US'}

    def __init__(self, base=PARENT_STYLE, **attributes):
        """Initialize this text style with the given style `attributes` and
        `base` style. The default (`base` = :const:`PARENT_STYLE`) is to inherit
        the style of the parent of the :class:`Styled` element."""
        super().__init__(base=base, **attributes)


class CharacterLike(Styled):
    def __init__(self, style=PARENT_STYLE):
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
    """Base class for text that has a :class:`TextStyle` associated with it."""

    style_class = TextStyle

    def __init__(self, style=PARENT_STYLE):
        """Initialise this styled text with the given `style`. The default
        (`style` = :const:`PARENT_STYLE`) is to inherit the style of the parent
        of this styled text."""
        super().__init__(style)
        self._y_offset = 0

    def __add__(self, other):
        """Return the concatenation of this styled text and `other`. If `other`
        is `None`, this styled text itself is returned."""
        return MixedStyledText([self, other]) if other is not None else self

    def __radd__(self, other):
        """Return the concatenation of `other` and this styled text. If `other`
        is `None`, this styled text itself is returned."""
        return MixedStyledText([other, self]) if other is not None else self

    def __iadd__(self, other):
        """Return the concatenation of this styled text and `other`. If `other`
        is `None`, this styled text itself is returned."""
        return self + other

    position = {SUPERSCRIPT: 1 / 3,
                SUBSCRIPT: - 1 / 6}
    position_size = 583 / 1000

    def is_script(self):
        """Returns `True` if this styled text is super/subscript."""
        try:
            return self.style.get('position') is not None
        except ParentStyleException:
            return False

    @property
    def script_level(self):
        """Nesting level of super/subscript."""
        level = self.parent.script_level if (self.parent is not None) else -1
        return level + 1 if self.is_script() else level

    @property
    def height(self):
        """Font size after super/subscript size adjustment."""
        height = float(self.get_style('font_size'))
        if self.script_level > -1:
            height *= self.position_size * (5 / 6)**self.script_level
        return height

    @property
    def y_offset(self):
        """Vertical baseline offset (up is positive)."""
        offset = self.parent.y_offset if (self.parent is not None) else 0
        if self.is_script():
            offset += self.parent.height * self.position[self.style.position]
            # The Y offset should only change once for the nesting level
            # where the position style is set, hence we don't recursively
            # get the position style using self.get_style('position')
        return offset


class SingleStyledText(StyledText):
    """Styled text where all text shares a single :class:`TextStyle`."""

    def __init__(self, text, style=PARENT_STYLE):
        """Initialise this single-styled text with the given `style`. The
        default (`style` = :const:`PARENT_STYLE`) is to inherit the style of the
        parent of this styled text."""
        super().__init__(style)
        self.text = re.sub('[\t\r\n ]+', ' ', text)

    def __repr__(self):
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.text, self.style)

    def __str__(self):
        return self.text

    def __getitem__(self, index):
        result = self.__class__(self.text[index])
        result.parent = self.parent
        return result

    def split(self):
        def is_special(char):
            return char in SPECIAL_CHARS.keys()

        for special, lst in itertools.groupby(self.text, is_special):
            if special:
                for char in lst:
                    item = SPECIAL_CHARS[char]()
                    item.parent = self
                    yield item
            else:
                item = self.__class__(''.join(lst))
                item.parent = self
                yield item

    @cached_property
    def font(self):
        """The :class:`Font` described by this styled text's style.

        If the exact font style, as determined by the `font_weight`,
        `font_slant` and `font_width` style attributes is not present in the
        `typeface`, the closest font available is returned instead, and a
        warning is issued."""
        typeface = self.get_style('typeface')
        weight = self.get_style('font_weight')
        slant = self.get_style('font_slant')
        width = self.get_style('font_width')
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
        hyphen_lang = self.get_style('hyphen_lang')
        hyphen_chars = self.get_style('hyphen_chars')
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
            hyphenator = self._hyphenator
            for position in reversed(hyphenator.positions(word)):
                parts = hyphenator.wrap(word, position + 1)
                if ''.join((parts[0][:-1], parts[1])) != word:
                    raise NotImplementedError
                first, second = self[:position], self[position:]
                first.text += '-'
                yield first, second

    def spans(self):
        span = self
        if self.get_style('small_caps'):
            span = SmallCapitalsText(span.text, span.style)
            span.parent = self.parent
        yield span


class SmallCapitalsText(SingleStyledText):
    def __init__(self, text, style=PARENT_STYLE):
        super().__init__(text, style)

    def glyphs(self):
        return super().glyphs(SMALL_CAPITAL)


class MixedStyledText(StyledText, list):
    def __init__(self, items, style=PARENT_STYLE):
        StyledText.__init__(self, style)
        if isinstance(items, str):
            items = [items]
        for item in items:
            self.append(item)

    def __repr__(self):
        return '{}{} (style={})'.format(self.__class__.__name__,
                                        super().__repr__(), self.style)

    def __str__(self):
        return ''.join(str(item) for item in self)

    def append(self, item):
        if isinstance(item, str):
            item = SingleStyledText(item, style=PARENT_STYLE)
        item.parent = self
        list.append(self, item)

    def spans(self):
        # TODO: support for mixed-style words
        # TODO: kerning between Glyphs
        for item in self:
            from .flowable import Flowable
            if isinstance(item, Flowable):
                yield item
            else:
                for span in item.spans():
                    yield span


class LiteralText(MixedStyledText):
    def __init__(self, text, style=PARENT_STYLE):
        text_with_no_break_spaces = text.replace(' ', chr(0xa0))
        items = intersperse(text_with_no_break_spaces.split('\n'), NewLine())
        super().__init__(items, style)

    def _clean_text(self, text):
        return text


# TODO: make following classes immutable (override setattr) and store widths
class Character(SingleStyledText):
    def __init__(self, text, style=PARENT_STYLE):
        super().__init__(text, style)

    def __str__(self):
        return self.text

    def split(self):
        yield self


class Space(Character):
    def __init__(self, fixed_width=False, style=PARENT_STYLE):
        super().__init__(' ', style)
        self.fixed_width = fixed_width


class FixedWidthSpace(Space):
    def __init__(self, style=PARENT_STYLE):
        super().__init__(True, style)


class NoBreakSpace(Character):
    def __init__(self, style=PARENT_STYLE):
        super().__init__(' ', style)


class Spacer(FixedWidthSpace):
    def __init__(self, dimension):
        super().__init__(style=None)
        self.dimension = dimension

    @property
    def widths(self):
        yield float(self.dimension)


SPECIAL_CHARS = {' ': Space,
                 chr(0xa0): NoBreakSpace}


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


class ControlCharacter(Character):
    def __init__(self, text):
        super().__init__(text)

    def __repr__(self):
        return self.__class__.__name__

    def spans(self):
        yield self


class NewLine(ControlCharacter):
    def __init__(self):
        super().__init__('\n')


class Tab(ControlCharacter):
    def __init__(self):
        super().__init__(' ')
        self.tab_width = 0


# predefined styles

EMPHASIZED_STYLE = TextStyle(font_slant=ITALIC)
BOLD_STYLE = TextStyle(font_weight=BOLD)
ITALIC_STYLE = TextStyle(font_slant=ITALIC)
BOLD_ITALIC_STYLE = TextStyle(font_weight=BOLD, font_slant=ITALIC)
SMALL_CAPITALS_STYLE = TextStyle(small_caps=True)
SUPERSCRIPT_STYLE = TextStyle(position=SUPERSCRIPT)
SUBSCRIPT_STYLE = TextStyle(position=SUBSCRIPT)


class Bold(MixedStyledText):
    def __init__(self, text):
        super().__init__(text, style=BOLD_STYLE)


class Italic(MixedStyledText):
    def __init__(self, text):
        super().__init__(text, style=ITALIC_STYLE)


class Emphasized(MixedStyledText):
    def __init__(self, text):
        super().__init__(text, style=ITALIC_STYLE)


class SmallCaps(MixedStyledText):
    def __init__(self, text):
        super().__init__(text, style=SMALL_CAPITALS_STYLE)


class Superscript(MixedStyledText):
    def __init__(self, text):
        super().__init__(text, style=SUPERSCRIPT_STYLE)


class Subscript(MixedStyledText):
    def __init__(self, text):
        super().__init__(text, style=SUBSCRIPT_STYLE)
