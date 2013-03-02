"""
Classes for describing styled text:

* :class:`SingleStyledText`: Text of a single style.
* :class:`MixedStyledText`: Text where different substrings can have different
                            styles.
* :class:`LiteralText`: Text that is typeset as is, including newlines and tabs.
* :class:`TextStyle`: Style class specifying the font and other styling of text.

A number of :class:`MixedStyledText` subclasses are provided for changing a
single style attribute of the passed text:

* :class:`Bold`
* :class:`Italic`
* :class:`Emphasized`
* :class:`SmallCaps`
* :class:`Superscript`
* :class:`Subscript`

Some characters with special properties and are represented by special classes:

* :class:`Space`
* :class:`FixedWidthSpace`
* :class:`NoBreakSpace`
* :class:`Spacer
* :class:`Tab`
* :class:`Newline`

"""

import os
import re

from functools import partial

from . import DATA_PATH
from .dimension import PT
from .flowable import Flowable
from .font.style import MEDIUM, UPRIGHT, NORMAL, BOLD, ITALIC
from .font.style import SUPERSCRIPT, SUBSCRIPT
from .font.style import SMALL_CAPITAL
from .fonts import adobe14
from .hyphenator import Hyphenator
from .style import Style, Styled, PARENT_STYLE, ParentStyleException
from .util import cached_property, cached_generator


__all__ = ['TextStyle', 'SingleStyledText', 'MixedStyledText', 'LiteralText',
           'Space', 'FixedWidthSpace', 'NoBreakSpace', 'Spacer',
           'Tab', 'Newline',
           'Bold', 'Italic', 'Emphasized', 'SmallCaps', 'Superscript',
           'Subscript']


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

    def __init__(self, style=PARENT_STYLE, parent=None):
        """Initialize this styled text with the given `style` and `parent` (see
        :class:`Styled`). The default (`style` = :const:`PARENT_STYLE`) is to
        inherit the style of the parent of this styled text. """
        super().__init__(style, parent)
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
        if self.style == PARENT_STYLE:
            return False
        else:
            return self.style.get('position') is not None

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

    def spans(self):
        """Generator yielding all of this styled text, one
        :class:`SingleStyledText` at a time (used in typesetting)."""
        raise NotImplementedError


class SingleStyledText(StyledText):
    """Styled text where all text shares a single :class:`TextStyle`."""

    def __init__(self, text, style=PARENT_STYLE, parent=None):
        """Initialize this single-styled text with `text` (:class:`str`),
        `style`, and `parent` (see :class:`StyledText`).

        In `text`, tab, line-feed and newline characters are all considered
        whitespace. Consecutive whitespace characters are reduced to a single
        space."""
        super().__init__(style=style, parent=parent)
        self.text = self._filter_text(text)

    @staticmethod
    def _filter_text(text):
        """Replace tabulator, line-feed and newline characters in `text` with
        spaces and afterwards reduce consecutive spaces with a single space."""
        return re.sub('[\t\r\n ]+', ' ', text)

    def __repr__(self):
        """Return a representation of this single-styled text; the text string
        along with a representation of its :class:`TextStyle`."""
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.text, self.style)

    def __len__(self):
        """Return the length (character count) of this single-styled text."""
        return len(self.text)

    def __str__(self):
        """Return the text content of this single-styled text."""
        return self.text

    def __getitem__(self, index):
        """Indexing/slicing into this single-styled text. Its style and parent
        are inherited by the result."""
        return self.__class__(self.text[index], parent=self.parent)

    def lower(self):
        """Return a lowercase version of this single-styled text."""
        return self.__class__(self.text.lower(),
                              style=self.style, parent=self.parent)

    def upper(self):
        """Return an uppercase version of this single-styled text."""
        return self.__class__(self.text.upper(),
                              style=self.style, parent=self.parent)

    def split(self):
        """Generator yielding words, whitespace and punctuation marks which make
        up this single-styled text. Yielded items inherit the style and parent
        from this single-styled text."""
        style_and_parent = {'style': self.style, 'parent': self.parent}
        part = ''
        for char in self.text:
            if char in SPECIAL_CHARS:
                if part:
                    yield self.__class__(part, **style_and_parent)
                yield SPECIAL_CHARS[char](**style_and_parent)
                part = ''
            else:
                part += char
        if part:
            yield self.__class__(part, **style_and_parent)

    @cached_property
    def font(self):
        """The :class:`Font` described by this single-styled text's style.

        If the exact font style as described by the `font_weight`,
        `font_slant` and `font_width` style attributes is not present in the
        `typeface`, the closest font available is returned instead, and a
        warning is printed."""
        typeface = self.get_style('typeface')
        weight = self.get_style('font_weight')
        slant = self.get_style('font_slant')
        width = self.get_style('font_width')
        return typeface.get(weight=weight, slant=slant, width=width)

    @property
    def width(self):
        """The total width of this single-styled text."""
        return sum(self.widths)

    @cached_property
    def widths(self):
        """A list of the widths of the individual glyphs in this single-styled
        text. Kerning adjustment (if enabled in the :class:`TextStyle`) between
        two glyphs is added to the width of the first glyph."""
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

    @cached_generator
    def glyphs(self):
        """Generator yielding the glyphs of this single-styled text, taking care
        of substituting ligatures where possible (if enabled in the
        :class:`TextStyle`)."""
        characters = iter(self.text)
        variant = SMALL_CAPITAL if self.get_style('small_caps') else None
        get_glyph = partial(self.font.metrics.get_glyph, variant=variant)
        get_ligature = self.font.metrics.get_ligature

        prev_glyph = get_glyph(next(characters))
        for char in characters:
            glyph = get_glyph(char)
            ligature = get_ligature(prev_glyph, glyph)
            if ligature:
                prev_glyph = ligature
            else:
                yield prev_glyph
                prev_glyph = glyph
        yield prev_glyph

    @property
    def _hyphenator(self):
        """Return a :class:`Hyphenator` configured with the hyphenation options
        specified in this single-styled text's :class:`TextStyle`.

        The hyphenation dictionary corresponding to the specified language is
        first searched in the current directory, then in RinohType's data
        directory."""
        hyphen_lang = self.get_style('hyphen_lang')
        hyphen_chars = self.get_style('hyphen_chars')
        dic_path = dic_file = 'hyph_{}.dic'.format(hyphen_lang)
        if not os.path.exists(dic_path):
            dic_path = os.path.join(os.path.join(DATA_PATH, 'hyphen'), dic_file)
            if not os.path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))
        return Hyphenator(dic_path, hyphen_chars, hyphen_chars)

    def hyphenate(self):
        """Generator yielding possible options for splitting this single-styled
        text (assuming it is a word) across two lines. Items yielded are tuples
        containing the first (with trailing hyphen) and second part of the split
        word.

        In the first returned option, the word is split at the right-most
        possible break point. In subsequent items, the break point advances to
        the front of the word.
        If hyphenation is not possible or simply not enabled, a single tuple is
        yielded of which the first element is the word itself, and the second
        element is `None`."""
        if self.get_style('hyphenate'):
            for first, second in self._hyphenator.iterate(self):
                if first.text + second.text != self.text:
                    raise NotImplementedError
                first.text += '-'
                yield first, second
        else:
            yield self, None

    def spans(self):
        """Yield this single-styled text itself."""
        yield self


class MixedStyledText(StyledText, list):
    """Concatenation of :class:`StyledText` objects."""

    def __init__(self, text_or_items, style=PARENT_STYLE, parent=None):
        """Initialize this mixed-styled text as the concatenation of
        `text_or_items`, which is either a single text item or an iterable of
        text items. Individual text items can be :class:`StyledText` or
        :class:`str` objects. This mixed-styled text is set as the parent of
        each of the text items.

        See :class:`StyledText` for information on `style`, and `parent`."""
        super().__init__(style=style, parent=parent)
        if (isinstance(text_or_items, str)
            or isinstance(text_or_items, StyledText)):
            text_or_items = (text_or_items, )
        for item in text_or_items:
            self.append(item)

    def __repr__(self):
        """Return a representation of this mixed-styled text; its children
        along with a representation of its :class:`TextStyle`."""
        return '{}{} (style={})'.format(self.__class__.__name__,
                                        super().__repr__(), self.style)

    def __str__(self):
        """Return the text content of this mixed-styled text."""
        return ''.join(str(item) for item in self)

    def append(self, item):
        """Append `item` (:class:`StyledText` or :class:`str`) to the end of
        this mixed-styled text.

        The parent of `item` is set to this mixed-styled text."""
        if isinstance(item, str):
            item = SingleStyledText(item, style=PARENT_STYLE)
        item.parent = self
        list.append(self, item)

    def spans(self):
        """Recursively yield all the :class:`SingleStyledText` items in this
        mixed-styled text."""
        # TODO: support for mixed-style words
        for item in self:
            if isinstance(item, Flowable):
                yield item
            else:
                for span in item.spans():
                    yield span


class StyledRawText(SingleStyledText):
    """Styled text that preserves tabs, newlines and spaces."""

    def __init__(self, text, style=PARENT_STYLE, parent=None):
        """Initialize this styled raw text with `text` (:class:`str`), `style`,
        and `parent` (see :class:`StyledText`)."""
        super().__init__(text, style=style, parent=parent)

    @staticmethod
    def _filter_text(text):
        """Return `text` as is."""
        return text


class LiteralText(StyledRawText):
    """Styled text which is typeset as is. No line wrapping is performed. Lines
    are split where a newline character appears in the literal text."""

    def __init__(self, text, style=PARENT_STYLE, parent=None):
        """Initialize this literal text with `text` (:class:`str`), `style`, and
        `parent` (see :class:`StyledText`)."""
        no_break_spaced = text.replace(' ', chr(0xa0))
        super().__init__(no_break_spaced, style=style, parent=parent)


class Character(StyledRawText):
    """:class:`SingleStyledText` consisting of a single character."""

    def split(self):
        """Yields this character itself."""
        yield self

    def hyphenate(self):
        """A single character can't be hyphenated."""
        yield self, None


class Space(Character):
    """A space character."""

    def __init__(self, fixed_width=False, style=PARENT_STYLE, parent=None):
        """Initialize this space. `fixed_width` specifies whether this space
        can be stretched (`False`) or not (`True`) in justified paragraphs.
        See :class:`StyledText` about `style` and `parent`."""
        super().__init__(' ', style=style, parent=parent)
        self.fixed_width = fixed_width


class FixedWidthSpace(Space):
    """A fixed-width space character."""

    def __init__(self, style=PARENT_STYLE, parent=None):
        """Initialize this fixed-width space with `style` and `parent` (see
        :class:`StyledText`)."""
        super().__init__(True, style=style, parent=parent)


class NoBreakSpace(Character):
    """Non-breaking space character.

    Lines cannot wrap at a this type of space."""

    def __init__(self, style=PARENT_STYLE, parent=None):
        """Initialize this non-breaking space with `style` and `parent` (see
        :class:`StyledText`)."""
        super().__init__(' ', style=style, parent=parent)


class Spacer(FixedWidthSpace):
    """A space of a specific width."""

    def __init__(self, width, style=PARENT_STYLE, parent=None):
        """Initialize this spacer at `width` with `style` and `parent` (see
        :class:`StyledText`)."""
        super().__init__(style=style, parent=parent)
        self._width = width

    @property
    def widths(self):
        """Generator yielding the width of this spacer."""
        yield float(self._width)


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
    """A non-printing character that affects typesetting of the text near it."""

    def __init__(self, char):
        """Initialize this control character with it's unicode `char`."""
        super().__init__(char)

    def __repr__(self):
        """A textual representation of this control character."""
        return self.__class__.__name__


class Newline(ControlCharacter):
    """Control character ending the current line and starting a new one."""

    def __init__(self, *args, **kwargs):
        """Initiatize this newline character."""
        super().__init__('\n')


class Tab(ControlCharacter):
    """Tabulator character, used for vertically aligning text."""

    def __init__(self, *args, **kwargs):
        """Initialize this tab character. Its attribute :attr:`tab_width` is set
        a later point in time when context (:class:`TabStop`) is available."""
        super().__init__(' ')
        self.tab_width = 0

    def expand(self):
        """Generator expanding this tab to either a spacer or a sequence of fill
        strings. The yielded items have a total width equal to the required tab
        width, as determined from the context.

        If the associated :class:`TabStop` has a fill string set, the items
        yielded consist of a sequence of these fill strings, preceeded by a
        :class:`Spacer` to pad to the tab width. If no fill string is set, only
        a single :class:`Spacer` is yielded."""
        style_and_parent = {'style': self.style, 'parent': self.parent}
        fill_string = self.tab_stop.fill
        if fill_string:
            fill_text = SingleStyledText(fill_string, **style_and_parent)
            number, rest = divmod(self.tab_width, fill_text.width)
            yield Spacer(rest, **style_and_parent)
            for i in range(int(number)):
                yield fill_text
        else:
            yield Spacer(self.tab_width, **style_and_parent)


SPECIAL_CHARS = {' ': Space,
                 '\t': Tab,
                 '\n': Newline}


# predefined text styles

ITALIC_STYLE = EMPHASIZED_STYLE = TextStyle(font_slant=ITALIC)
BOLD_STYLE = TextStyle(font_weight=BOLD)
BOLD_ITALIC_STYLE = TextStyle(font_weight=BOLD, font_slant=ITALIC)
SMALL_CAPITALS_STYLE = TextStyle(small_caps=True)
SUPERSCRIPT_STYLE = TextStyle(position=SUPERSCRIPT)
SUBSCRIPT_STYLE = TextStyle(position=SUBSCRIPT)


class Bold(MixedStyledText):
    """Bold text."""

    def __init__(self, text):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=BOLD_STYLE)


class Italic(MixedStyledText):
    """Italic text."""

    def __init__(self, text):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=ITALIC_STYLE)


class Emphasized(MixedStyledText):
    """Emphasized text."""

    def __init__(self, text):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=ITALIC_STYLE)


class SmallCaps(MixedStyledText):
    """Small capitals text."""

    def __init__(self, text):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=SMALL_CAPITALS_STYLE)


class Superscript(MixedStyledText):
    """Superscript."""

    def __init__(self, text):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=SUPERSCRIPT_STYLE)


class Subscript(MixedStyledText):
    """Subscript."""

    def __init__(self, text):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=SUBSCRIPT_STYLE)
