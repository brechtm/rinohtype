# This file is part of rinohtype, the Python document preparation system.
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

import re

from ast import literal_eval
from html.entities import name2codepoint
from itertools import tee

from .attribute import (AttributeType, Attribute, Bool, Integer,
                        AcceptNoneAttributeType)
from .color import Color, BLACK
from .dimension import Dimension, PT
from .font import Typeface
from .fonts import adobe14
from .font.style import (FontWeight, FontSlant, FontWidth, FontVariant,
                         TextPosition)
from .style import Style, Styled, PARENT_STYLE, StyleException


__all__ = ['TextStyle', 'StyledText', 'SingleStyledText', 'MixedStyledText',
           'ConditionalMixedStyledText', 'Space', 'FixedWidthSpace',
           'NoBreakSpace', 'Spacer', 'Tab', 'Newline',
           'Superscript', 'Subscript']


class Locale(AttributeType):
    REGEX = re.compile(r'^[a-z]{2}_[A-Z]{2}$')

    @classmethod
    def check_type(cls, value):
        return cls.REGEX.match(value) is not None

    @classmethod
    def parse_string(cls, string):
        if not cls.check_type(string):
            raise ValueError("'{}' is not a valid locale. Needs to be of the "
                             "form 'en_US'.".format(string))
        return string

    @classmethod
    def doc_format(cls):
        return 'locale identifier in the ``<language ID>_<region ID>`` format'


class TextStyle(Style):
    typeface = Attribute(Typeface, adobe14.times, 'Typeface to set the text in')
    font_weight = Attribute(FontWeight, 'medium', 'Thickness of character '
                                                  'outlines relative to their '
                                                  'height')
    font_slant = Attribute(FontSlant, 'upright', 'Slope style of the font')
    font_width = Attribute(FontWidth, 'normal', 'Stretch of the characters')
    font_size = Attribute(Dimension, 10*PT, 'Height of characters')
    font_color = Attribute(Color, BLACK, 'Color of the font')
    font_variant = Attribute(FontVariant, 'normal', 'Variant of the font')
    position = Attribute(TextPosition, 'normal', 'Vertical text position')
    kerning = Attribute(Bool, True, 'Improve inter-letter spacing')
    ligatures = Attribute(Bool, True, 'Run letters together where possible')
    # TODO: character spacing
    hyphenate = Attribute(Bool, True, 'Allow words to be broken over two lines')
    hyphen_chars = Attribute(Integer, 2, 'Minimum number of characters in a '
                                         'hyphenated part of a word')
    hyphen_lang = Attribute(Locale, 'en_US', 'Language to use for hyphenation. '
                                             'Accepts locale codes such as '
                                             "'en_US'")

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


NAME2CHAR = {name: chr(codepoint)
             for name, codepoint in name2codepoint.items()}


class StyledText(Styled, AcceptNoneAttributeType):
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

    @classmethod
    def check_type(cls, value):
        return super().check_type(value) or isinstance(value, str)

    @classmethod
    def parse_string(cls, string):
        def parse_text(chars):
            text = quote = skip_whitespace(chars)
            if not quote in ("'", '"'):
                raise StyledTextParseError
            escape = False
            for char in chars:
                text += char
                if not escape and char == quote:
                    return text
                escape = char == '\\'
            raise StyledTextParseError('Missing closing quote')

        def parse_style(chars):
            chars, saved_chars = tee(chars)
            try:
                next_char = skip_whitespace(chars)
            except StopIteration:
                return saved_chars, None
            if next_char != '(':
                return saved_chars, None
            style = ''
            for char in chars:
                if char == ')':
                    return chars, style
                else:
                    style += char
            raise StyledTextParseError('Missing closing brace')

        def skip_whitespace(chars):
            for char in chars:
                if char not in ' \t':
                    return char
            raise StopIteration

        texts = []
        chars = iter(string.strip())
        while True:
            try:
                text = literal_eval(parse_text(chars))
                chars, style = parse_style(chars)
                texts.append(cls._substitute_variables(text, style))
            except StopIteration:
                break

        if len(texts) > 1:
            return MixedStyledText(texts)
        else:
            first, = texts
            return first

    @classmethod
    def doc_repr(cls, value):
        return '``{}``'.format(value) if value else '(no value)'

    @classmethod
    def doc_format(cls):
        return ("a list of styled text strings, separated by spaces. A styled "
                "text string is a quoted string (``'`` or ``\"``), optionally "
                "followed by a style name enclosed in braces: "
                "``'text string' (style name)``")

    @classmethod
    def validate(cls, value, accept_variables=False, attribute_name=None):
        if attribute_name is None and isinstance(value, str):
            value = SingleStyledText(value)
        return super().validate(value, accept_variables, attribute_name)

    @classmethod
    def _substitute_variables(cls, text, style):
        def substitute_html_entities(string, style=None):
            return SingleStyledText(string.format(**NAME2CHAR), style=style)

        return Field.substitute(text, substitute_html_entities, style=style)

    def __str__(self):
        return self.to_string(None)

    def _short_repr_args(self, flowable_target):
        yield self._short_repr_string(flowable_target)

    def to_string(self, flowable_target):
        """Return the text content of this styled text."""
        raise NotImplementedError('{}.to_string'.format(type(self).__name__))

    @property
    def paragraph(self):
        return self.parent.paragraph

    position = {TextPosition.SUPERSCRIPT: 1 / 3,
                TextPosition.SUBSCRIPT: - 1 / 6}
    position_size = 583 / 1000

    def is_script(self, container):
        """Returns `True` if this styled text is super/subscript."""
        try:
            style = self._style(container)
            return style.get_value('position',
                                   container) != TextPosition.NORMAL
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

    @property
    def items(self):
        """The list of items in this StyledText."""
        raise NotImplementedError

    def spans(self, container):
        """Generator yielding all spans in this styled text, one
        item at a time (used in typesetting)."""
        raise NotImplementedError


class StyledTextParseError(Exception):
    pass


class SingleStyledTextBase(StyledText):
    """Styled text where all text shares a single :class:`TextStyle`."""

    def __repr__(self):
        """Return a representation of this single-styled text; the text string
        along with a representation of its :class:`TextStyle`."""
        return "{0}('{1}', style={2})".format(self.__class__.__name__,
                                              self.text(None), self.style)

    def text(self, flowable_target, **kwargs):
        raise NotImplementedError

    def to_string(self, flowable_target):
        return self.text(flowable_target)

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

    @property
    def items(self):
        return [self]

    def spans(self, container):
        yield self


ESCAPE = str.maketrans({"'": r"\'",
                        '\n': r'\n',
                        '\t': r'\t'})


class SingleStyledText(SingleStyledTextBase):
    def __init__(self, text, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._text = text

    def __str__(self):
        result = "'{}'".format(self._text.translate(ESCAPE))
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def text(self, container, **kwargs):
        return self._text


class MixedStyledTextBase(StyledText):
    def to_string(self, flowable_target):
        return ''.join(item.to_string(flowable_target)
                       for item in self.children(flowable_target))

    def spans(self, container):
        """Recursively yield all the :class:`SingleStyledText` items in this
        mixed-styled text."""
        for child in self.children(container):
            container.register_styled(child)
            for span in child.spans(container):
                yield span

    def children(self, flowable_target):
        raise NotImplementedError


class MixedStyledText(MixedStyledTextBase, list):
    """Concatenation of styled text

    Args:
        text_or_items (str, StyledText or iterable of these): mixed styled text
        style: see :class:`.Styled`
        parent: see :class:`.DocumentElement`

    """

    _assumed_equal = {}

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

    def __add__(self, other):
        if isinstance(other, str):
            other = SingleStyledText(other)
        if self.style == other.style:
            return MixedStyledText(self.items + other.items,
                                   style=self.style, parent=self.parent)
        else:
            return super().__add__(other)

    def __repr__(self):
        """Return a representation of this mixed-styled text; its children
        along with a representation of its :class:`TextStyle`."""
        return '{}{} (style={})'.format(self.__class__.__name__,
                                        super().__repr__(), self.style)

    def __str__(self):
        assert self.style is None
        return ' '.join(str(item) for item in self)

    def __eq__(self, other):
        # avoid infinite recursion due to the 'parent' attribute
        assumed_equal = type(self)._assumed_equal.setdefault(id(self), set())
        other_id = id(other)
        if other_id in assumed_equal:
            return True
        try:
            assumed_equal.add(other_id)
            return super().__eq__(other) and list.__eq__(self, other)
        finally:
            assumed_equal.remove(other_id)

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

    @property
    def items(self):
        return list(self)

    def children(self, flowable_target):
        return self.items


class ConditionalMixedStyledText(MixedStyledText):
    def __init__(self, text_or_items, document_option, style=None, parent=None):
        super().__init__(text_or_items, style=style, parent=parent)
        self.document_option = document_option

    def spans(self, container):
        if container.document.options[self.document_option]:
            for span in super().spans(container):
                yield span


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

SUPERSCRIPT_STYLE = TextStyle(position='superscript')
SUBSCRIPT_STYLE = TextStyle(position='subscript')


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


from .reference import Field
