# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

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

from itertools import groupby

from .color import BLACK
from .dimension import PT
from .font.style import MEDIUM, UPRIGHT, NORMAL, BOLD, ITALIC
from .font.style import SUPERSCRIPT, SUBSCRIPT
from .fonts import adobe14
from .style import Style, Styled, PARENT_STYLE, StyleException


__all__ = ['TextStyle', 'StyledText', 'SingleStyledText', 'MixedStyledText',
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
                  'font_color': BLACK,
                  'small_caps': False,
                  'position': None,
                  'kerning': True,
                  'ligatures': True,
                  # TODO: character spacing
                  'hyphenate': True,
                  'hyphen_chars': 2,
                  'hyphen_lang': 'en_US'}

    default_base = PARENT_STYLE


class CharacterLike(Styled):
    def __repr__(self):
        return "{0}(style={1})".format(self.__class__.__name__, self.style)

    @property
    def width(self):
        raise NotImplementedError

    def height(self, document):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError


class StyledText(Styled):
    """Base class for text that has a :class:`TextStyle` associated with it."""

    style_class = TextStyle

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

    def is_script(self, container):
        """Returns `True` if this styled text is super/subscript."""
        try:
            style = self._style(container)
            return style.get_value('position', container) is not None
        except StyleException:
            return False

    def script_level(self, container):
        """Nesting level of super/subscript."""
        try:
            level = self.parent.script_level(container)
        except AttributeError:
            level = -1
        return level + 1 if self.is_script(container) else level

    def height(self, container):
        """Font size after super/subscript size adjustment."""
        height = float(self.get_style('font_size', container))
        script_level = self.script_level(container)
        if script_level > -1:
            height *= self.position_size * (5 / 6)**script_level
        return height

    def y_offset(self, container):
        """Vertical baseline offset (up is positive)."""
        offset = (self.parent.y_offset(container)\
                  if hasattr(self.parent, 'y_offset') else 0)
        if self.is_script(container):
            style = self._style(container)
            offset += (self.parent.height(container) *
                       self.position[style.position])
            # The Y offset should only change once for the nesting level
            # where the position style is set, hence we don't recursively
            # get the position style using self.get_style('position')
        return offset

    def spans(self):
        """Generator yielding all spans in this styled text, one
        item at a time (used in typesetting)."""
        raise NotImplementedError


class SingleStyledText(StyledText):
    """Styled text where all text shares a single :class:`TextStyle`."""

    def __init__(self, text, style=None, parent=None):
        """Initialize this single-styled text with `text` (:class:`str`),
        `style`, and `parent` (see :class:`StyledText`).

        In `text`, tab, line-feed and newline characters are all considered
        whitespace. Consecutive whitespace characters are reduced to a single
        space."""
        super().__init__(style=style, parent=parent)
        self.text = text

    def __repr__(self):
        """Return a representation of this single-styled text; the text string
        along with a representation of its :class:`TextStyle`."""
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.text, self.style)

    def __str__(self):
        """Return the text content of this single-styled text."""
        return self.text

    def font(self, container):
        """The :class:`Font` described by this single-styled text's style.

        If the exact font style as described by the `font_weight`,
        `font_slant` and `font_width` style attributes is not present in the
        `typeface`, the closest font available is returned instead, and a
        warning is printed."""
        typeface = self.get_style('typeface', container)
        weight = self.get_style('font_weight', container)
        slant = self.get_style('font_slant', container)
        width = self.get_style('font_width', container)
        return typeface.get_font(weight=weight, slant=slant, width=width)

    def ascender(self, container):
        return (self.font(container).ascender_in_pt
                * float(self.get_style('font_size', container)))

    def descender(self, container):
        return (self.font(container).descender_in_pt
                * float(self.get_style('font_size', container)))

    def line_gap(self, container):
        return (self.font(container).line_gap_in_pt
                * float(self.get_style('font_size', container)))

    def spans(self, document):
        yield self

    @staticmethod
    def split_words(text):
        def is_special_character(char):
            return char in ' \t\n\N{ZERO WIDTH SPACE}'

        for is_special, characters in groupby(text, is_special_character):
            if is_special:
                for char in characters:
                    yield char
            else:
                yield ''.join(characters)

    def split(self, container):
        """Yield the words and spaces in this single-styled text."""
        return self.split_words(self.text)

    def before_placing(self, container):
        pass


class MixedStyledText(StyledText, list):
    """Concatenation of :class:`StyledText` objects."""

    def __init__(self, text_or_items, style=None, parent=None):
        """Initialize this mixed-styled text as the concatenation of
        `text_or_items`, which is either a single text item or an iterable of
        text items. Individual text items can be :class:`StyledText` or
        :class:`str` objects. This mixed-styled text is set as the parent of
        each of the text items.

        See :class:`StyledText` for information on `style`, and `parent`."""
        super().__init__(style=style, parent=parent)
        if isinstance(text_or_items, (str, StyledText)):
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

    def prepare(self, flowable_target):
        for item in self:
            item.prepare(flowable_target)

    def append(self, item):
        """Append `item` (:class:`StyledText` or :class:`str`) to the end of
        this mixed-styled text.

        The parent of `item` is set to this mixed-styled text."""
        if isinstance(item, str):
            item = SingleStyledText(item)
        item.parent = self
        list.append(self, item)

    def spans(self, document):
        """Recursively yield all the :class:`SingleStyledText` items in this
        mixed-styled text."""
        return (span for item in self for span in item.spans(document))


class Character(SingleStyledText):
    """:class:`SingleStyledText` consisting of a single character."""


class Space(Character):
    """A space character."""

    def __init__(self, fixed_width=False, style=None, parent=None):
        """Initialize this space. `fixed_width` specifies whether this space
        can be stretched (`False`) or not (`True`) in justified paragraphs.
        See :class:`StyledText` about `style` and `parent`."""
        super().__init__(' ', style=style, parent=parent)
        self.fixed_width = fixed_width


class FixedWidthSpace(Space):
    """A fixed-width space character."""

    def __init__(self, style=None, parent=None):
        """Initialize this fixed-width space with `style` and `parent` (see
        :class:`StyledText`)."""
        super().__init__(True, style=style, parent=parent)


class NoBreakSpace(Character):
    """Non-breaking space character.

    Lines cannot wrap at a this type of space."""

    def __init__(self, style=None, parent=None):
        """Initialize this non-breaking space with `style` and `parent` (see
        :class:`StyledText`)."""
        super().__init__(' ', style=style, parent=parent)


class Spacer(FixedWidthSpace):
    """A space of a specific width."""

    def __init__(self, width, style=None, parent=None):
        """Initialize this spacer at `width` with `style` and `parent` (see
        :class:`StyledText`)."""
        super().__init__(style=style, parent=parent)
        self._width = width

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

    def height(self, document):
        return self._height

    def render(self, canvas, x, y):
        box_canvas = canvas.new(x, y - self.depth, self.width,
                                self.height + self.depth)
        print(self.ps, file=box_canvas.psg_canvas)
        canvas.append(box_canvas)
        return self.width


class ControlCharacter(Character):
    """A non-printing character that affects typesetting of the text near it."""

    exception = Exception

    def __init__(self, char):
        """Initialize this control character with it's unicode `char`."""
        super().__init__(char)

    def __repr__(self):
        """A textual representation of this control character."""
        return self.__class__.__name__

    @property
    def width(self):
        """Raises the exception associated with this control character.

        This method is called during typesetting."""
        raise self.exception


class NewlineException(Exception):
    """Exception signaling a :class:`Newline`."""


class Newline(ControlCharacter):
    """Control character ending the current line and starting a new one."""

    exception = NewlineException

    def __init__(self, *args, **kwargs):
        """Initiatize this newline character."""
        super().__init__('\n')


class Tab(ControlCharacter):
    """Tabulator character, used for vertically aligning text."""

    def __init__(self, *args, **kwargs):
        """Initialize this tab character. Its attribute :attr:`tab_width` is set
        a later point in time when context (:class:`TabStop`) is available."""
        super().__init__('\t')


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

    def __init__(self, text, parent=None):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=ITALIC_STYLE, parent=parent)


class Emphasized(MixedStyledText):
    """Emphasized text."""

    def __init__(self, text, parent=None):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=EMPHASIZED_STYLE, parent=parent)


class SmallCaps(MixedStyledText):
    """Small capitals text."""

    def __init__(self, text, parent=None):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=SMALL_CAPITALS_STYLE, parent=parent)


class Superscript(MixedStyledText):
    """Superscript."""

    def __init__(self, text, parent=None):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=SUPERSCRIPT_STYLE, parent=parent)


class Subscript(MixedStyledText):
    """Subscript."""

    def __init__(self, text, parent=None):
        """Accepts a single instance of :class:`str` or :class:`StyledText`, or
        an iterable of these."""
        super().__init__(text, style=SUBSCRIPT_STYLE, parent=parent)
