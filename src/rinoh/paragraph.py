# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""

Classes for representing and typesetting paragraphs

"""

import re

from ast import literal_eval
from collections.abc import Iterable
from collections import namedtuple
from copy import copy
from itertools import chain, count
from os import path

from . import DATA_PATH
from .annotation import AnnotatedSpan
from .attribute import (Attribute, AttributeType, OptionSet, ParseError,
                        OverrideDefault, Integer)
from .dimension import Dimension, PT
from .flowable import Flowable, FlowableStyle, FlowableState, FlowableWidth
from .font import MissingGlyphException
from .hyphenator import Hyphenator
from .inline import InlineFlowable
from .layout import EndOfContainer, ContainerOverflow
from .number import NumberStyle, Label, format_number
from .strings import StringField
from .text import (TextStyle, StyledText, SingleStyledText, MixedStyledText,
                   SpanMetrics, ESCAPE, LANGUAGE_DEFAULT)
from .util import all_subclasses, ReadAliasAttribute


__all__ = ['Paragraph', 'ParagraphStyle', 'TabStop',
           'ProportionalSpacing', 'FixedSpacing', 'Leading',
           'DEFAULT', 'STANDARD', 'SINGLE', 'DOUBLE']


# Text justification

class TextAlign(OptionSet):
    """Text justification"""

    values = 'left', 'right', 'center', 'justify'


# Line spacing

class LineSpacing(AttributeType):
    """Base class for line spacing types

    Line spacing is defined as the distance between the baselines of two
    consecutive lines of text in a paragraph.

    """

    def __repr__(self):
        args = ', '.join(repr(arg) for arg in self._str_args)
        return '{}({})'.format(type(self).__name__, args)

    def __str__(self):
        for name, spacing in PREDEFINED_SPACINGS.items():
            if self is spacing:
                return name
        label = type(self).__name__.lower().replace('spacing', '')
        args = ', '.join(str(arg) for arg in self._str_args)
        return label + ('({})'.format(args) if args else '')

    @property
    def _str_args(self):
        raise NotImplementedError

    REGEX = re.compile(r'^(?P<type>[a-z]+)(\((?P<arg>.*)\))?$', re.I)

    @classmethod
    def parse_string(cls, string, source):
        m = cls.REGEX.match(string)
        if not m:
            raise ParseError("'{}' is not a valid {} type"
                             .format(string, cls.__name__))
        spacing_type = m.group('type').lower()
        arg_strings = m.group('arg').split(',') if m.group('arg') else ()
        if spacing_type in PREDEFINED_SPACINGS:
            if arg_strings:
                raise ParseError("'{}' takes no arguments"
                                 .format(spacing_type))
            return PREDEFINED_SPACINGS[spacing_type]
        for subcls in all_subclasses(cls):
            if subcls.__name__.lower().replace('spacing', '') == spacing_type:
                stripped_args = (arg.strip() for arg in arg_strings)
                try:
                    args = subcls.parse_arguments(*stripped_args)
                except TypeError as error:
                    raise ParseError("Incorrect number or type of arguments "
                                     "passed to '{}'".format(spacing_type))
                return subcls(*args)
        raise ParseError("'{}' is not a valid {}".format(string, cls.__name__))

    @classmethod
    def parse_arguments(cls, arg_strings):
        raise NotImplementedError

    @classmethod
    def doc_format(cls):
        return ('a :ref:`predefined line spacing <predefined_line_spacings>` '
                'type or the name of a line spacing type followed by comma-'
                'separated arguments enclosed in braces: '
                '``<spacing type>(<arg1>, <arg2>, ...)``')

    def advance(self, line, last_descender, container):
        """Return the distance between the descender of the previous line and
        the baseline of the current line."""
        raise NotImplementedError


class DefaultSpacing(LineSpacing):
    """The default line spacing as specified by the font."""

    @property
    def _str_args(self):
        return ()

    def advance(self, line, last_descender, container):
        return line.ascender + line.line_gap


DEFAULT = DefaultSpacing()
"""The default line spacing as specified by the font."""


class ProportionalSpacing(LineSpacing):
    """Line spacing proportional to the line height

    Args:
        factor (float): amount by which the line height is multiplied to obtain
            the line spacing

    """

    def __init__(self, factor):
        self.factor = factor

    @property
    def _str_args(self):
        return (self.factor, )

    @classmethod
    def parse_arguments(cls, factor):
        try:
            return float(factor),
        except ValueError:
            raise ParseError("'factor' parameter of 'proportional' should be "
                             "a floating point number")

    def advance(self, line, last_descender, container):
        return self.factor * line.height + last_descender


STANDARD = ProportionalSpacing(1.2)
"""Line spacing of 1.2 times the line height."""


SINGLE = ProportionalSpacing(1.0)
"""Line spacing equal to the line height (no leading)."""


DOUBLE = ProportionalSpacing(2.0)
"""Line spacing of double the line height."""


class FixedSpacing(LineSpacing):
    """Fixed line spacing, with optional minimum spacing

    Args:
        pitch (Dimension): the distance between the baseline of two consecutive
            lines of text
        minimum (LineSpacing): the minimum line spacing to prevents lines with
            large fonts (or inline elements) from overlapping; set to ``None``
            if no minimum is required, set to `None`

    """

    def __init__(self, pitch, minimum=SINGLE):
        self.pitch = pitch
        self.minimum = minimum

    @property
    def _str_args(self):
        if self.minimum is SINGLE:
            return (self.pitch, )
        else:
            return (self.pitch, self.minimum)

    @classmethod
    def parse_arguments(cls, pitch_str, minimum_str=None):
        pitch = Dimension.from_string(pitch_str)
        if minimum_str:
            minimum = LineSpacing.from_string(minimum_str)
            return pitch, minimum
        return pitch,

    def advance(self, line, last_descender, container):
        advance = float(self.pitch) + last_descender
        if self.minimum is not None:
            minimum = self.minimum.advance(line, last_descender, container)
            return max(advance, minimum)
        else:
            return advance


class Leading(LineSpacing):
    """Line spacing determined by the space in between two lines

    Args:
        leading (Dimension): the space between the bottom of a line and the top
            of the next line of text

    """

    def __init__(self, leading):
        self.leading = leading

    @property
    def _str_args(self):
        return (self.leading, )

    @classmethod
    def parse_arguments(cls, leading_str):
        leading = Dimension.from_string(leading_str)
        return leading,

    def advance(self, line, last_descender, container):
        return line.ascender + float(self.leading)


PREDEFINED_SPACINGS = dict(default=DEFAULT,
                           standard=STANDARD,
                           single=SINGLE,
                           double=DOUBLE)


class TabAlign(OptionSet):
    """Alignment of text with respect to a tab stop"""

    values = 'left', 'right', 'center'


class TabStop(object):
    """Horizontal position for aligning text of successive lines

    Args:
        position (:class:`Dimension` or :class:`Fraction`): tab stop position
        align (TabAlign): the alignment of text with respect to the tab stop
            position
        fill (str): string pattern to fill the empty tab space with

    """

    def __init__(self, position, align='left', fill=None):
        self._position = position
        self.align = align
        self.fill = fill

    def __repr__(self):
        fill_repr = None if self.fill is None else "'{}'".format(self.fill)
        return "{}({}, {}, {})".format(type(self).__name__, self._position,
                                       self.align.upper(), fill_repr)

    def __str__(self):
        result = '{} {}'.format(self._position, self.align)
        if self.fill:
            result += " '{}'".format(self.fill.translate(ESCAPE))
        return result

    def get_position(self, line_width):
        """Return the absolute position of this tab stop."""
        return self._position.to_points(line_width)


class TabStopList(AttributeType, list):
    """List of tab stop positions (with alignment and fill string)"""

    def __str__(self):
        return ', '.join(str(tab_stop) for tab_stop in self)

    @classmethod
    def check_type(cls, value):
        return (isinstance(value, (list, tuple))
                and all(isinstance(item, TabStop) for item in value))

    REGEX = re.compile(r"""\s*                     # leading whitespace
                           (?P<position>{pos})     # tab stop position

                           (?:                     ## optional: tab alignment
                             \s+                   # whitespace
                             (?P<align>{align})    # tab alignment
                           )?
                           (?:                     ## optional: fill string
                             \s+                   # whitespace
                             (?P<fill>.+)          # fill string
                           )?
                           (?:                     ## optional: separator
                             \s*                   # whitespace
                             ,                     # separating comma
                             \s*                   # whitespace
                           )?
                       """.format(pos=Dimension.REGEX.pattern,
                                  align='|'.join(TabAlign.values)),
                       re.IGNORECASE | re.VERBOSE)

    @classmethod
    def parse_string(cls, string, source):
        tabstops = []
        i = 0
        while string[i:]:
            m = cls.REGEX.match(string, pos=i)
            if not m:
                raise ValueError("'{}' is not a valid tab stop definition"
                                 .format(string, cls.__name__))
            _, i = m.span()
            position, align, fill = m.group('position', 'align', 'fill')
            tabstop = TabStop(Dimension.from_string(position),
                              TabAlign.from_string(align) if align else 'left',
                              literal_eval(fill) if fill else None)
            tabstops.append(tabstop)
        return cls(tabstops)

    @classmethod
    def doc_format(cls):
        return ('a comma-seperated list of tab stops. A tab stop is specified '
                'as ``<position> [align] [fill string]``, where '
                '``position`` (:class:`.Dimension`) is required and '
                '``align`` (:class:`.TabAlign`) and ``fill string`` '
                '(string enclosed in quotes) are optional.')


# TODO: look at Word/OpenOffice for more options
class ParagraphStyle(FlowableStyle, NumberStyle, TextStyle):
    width = OverrideDefault('fill')

    indent_first = Attribute(Dimension, 0*PT, 'Indentation of the first line '
                                              'of text')
    line_spacing = Attribute(LineSpacing, DEFAULT, 'Spacing between the '
                             'baselines of two successive lines of text')
    text_align = Attribute(TextAlign, 'justify', 'Alignment of text to the '
                                                 'margins')
    tab_stops = Attribute(TabStopList, TabStopList(), 'List of tab positions')
    split_minimum_lines = Attribute(Integer, 0,
                                    'Minimum number of lines to keep together'
                                    ' when splitting a paragraph across pages')
    number_format = OverrideDefault(None)
    number_separator = Attribute(StyledText, '.',
                                 "Characters inserted between the number label"
                                 " of this element's parent and this element's"
                                 " own number label. If ``None``, only show"
                                 " this item's number label.")
    numbering_level = Attribute(Integer, 0, 'At which section level to '
                                            'restart numbering (positive: '
                                            'absolute, negative: relative)')


class TextMetrics(SpanMetrics):
    """The metrics of a span of text and the shaper for its characters

    These are looked up only once for each computed style (see
    :func:`text_metrics`), since this requires resolving many of the span's
    style attributes.

    """

    __slots__ = ('font', 'color', 'y_offset', 'shaper')

    def __init__(self, span, container):
        font = span.font(container)
        font_size = float(span.get_style('font_size', container))
        height = span.height(container)
        super().__init__(font.ascender_in_pt * font_size,
                         font.descender_in_pt * font_size, height,
                         font.line_gap_in_pt * font_size)
        self.font = font
        self.color = span.get_style('font_color', container)
        self.y_offset = span.y_offset(container)
        key = (font, height, span.get_style('font_variant', container),
               span.get_style('kerning', container),
               span.get_style('ligatures', container),
               float(span.get_style('character_spacing', container)))
        shapers = container.document.shapers
        try:
            self.shaper = shapers[key]
        except KeyError:
            self.shaper = shapers[key] = Shaper(*key)


def text_metrics(span, container):
    """Return the :class:`TextMetrics` for `span`

    These are shared by all spans with the same computed style.

    """
    computed_style = container.document.get_computed_style(span)
    if computed_style.text_metrics is None:
        computed_style.text_metrics = TextMetrics(span, container)
    return computed_style.text_metrics


class Shaper(object):
    """Sets strings in the glyphs of `font` at `size` and measures them

    A shaper is shared by all text styles that select the same font, size
    and font features (see :class:`TextMetrics`). It shapes each distinct
    string only once.

    """

    def __init__(self, font, size, variant, kerning, ligatures,
                 character_spacing):
        self.font = font
        self.size = size
        self.variant = variant
        self.kerning = kerning
        self.ligatures = ligatures
        self.character_spacing = character_spacing
        self.scale = size / font.units_per_em
        self.space_glyph = self.glyph(' ')
        self.space_width = (self.scale * (self.space_glyph.width + 0.0)
                            + character_spacing)
        self._shaped = {}
        self.space = self.shape(' ')

    def glyph(self, char):
        return self.font.get_glyph_metrics(char, self.variant)

    def glyphs(self, string):
        """Set `string`, applying ligatures, kerning and character spacing

        Returns:
            (list, list, list): the glyphs, their widths and the characters
            each glyph represents

        """
        # TODO: handle ligatures at span borders
        chars = list(string)
        glyphs = [self.glyph(char) for char in chars]
        if self.ligatures and glyphs:
            get_ligature = self.font.get_ligature
            lig_chars, lig_glyphs = chars[:1], glyphs[:1]
            for char, glyph in zip(chars[1:], glyphs[1:]):
                ligature = get_ligature(lig_glyphs[-1], glyph)
                if ligature:
                    lig_chars[-1] += char
                    lig_glyphs[-1] = ligature
                else:
                    lig_chars.append(char)
                    lig_glyphs.append(glyph)
            chars, glyphs = lig_chars, lig_glyphs
        scale, spacing = self.scale, self.character_spacing
        if self.kerning and glyphs:
            get_kerning = self.font.get_kerning
            widths = [scale * (glyph.width + get_kerning(glyph, next_glyph))
                      + spacing
                      for glyph, next_glyph in zip(glyphs, glyphs[1:])]
            widths.append(scale * (glyphs[-1].width + 0.0) + spacing)
        else:
            widths = [scale * (glyph.width + 0.0) + spacing
                      for glyph in glyphs]
        return glyphs, widths, chars

    def shape(self, string):
        """Return the :class:`ShapedString` for `string`"""
        try:
            return self._shaped[string]
        except KeyError:
            shaped = self._shaped[string] = ShapedString(self, string)
            return shaped


class ShapedString(object):
    """A string set in the glyphs of a :class:`Shaper`

    Spaces are set in the shaper's space glyph, so that these can be
    stretched to justify a line; their entries in :attr:`widths` are `None`.

    """

    __slots__ = ('shaper', 'string', 'glyphs', 'widths', 'width', 'nspaces',
                 'ends_with_space', '_segments')

    def __init__(self, shaper, string):
        glyphs, widths, chars = shaper.glyphs(string) if string else ((), (),
                                                                       ())
        spaces = [char == ' ' for char in chars]
        self.shaper = shaper
        self.string = string
        self.glyphs = [shaper.space_glyph if space else glyph
                       for glyph, space in zip(glyphs, spaces)]
        self.widths = [None if space else width
                       for width, space in zip(widths, spaces)]
        self.width = sum(shaper.space_width if space else width
                         for width, space in zip(widths, spaces))
        self.nspaces = sum(spaces)
        self.ends_with_space = bool(spaces) and spaces[-1]
        self._segments = None if string else ['']

    def segments(self, canvas, document):
        """The encoded glyphs (see :meth:`Canvas.encode_glyphs`) in between
        the spaces"""
        if self._segments:
            return self._segments
        shaper = self.shaper
        space_width = shaper.space_width
        fragments = canvas.encode_glyphs(
            document, shaper.font, shaper.size,
            zip(self.glyphs, (space_width if width is None else width
                              for width in self.widths)))
        segments, segment = [], []
        for fragment, width in zip(fragments, self.widths):
            if width is None:
                segments.append(''.join(segment))
                segment.clear()
            else:
                segment.append(fragment)
        segments.append(''.join(segment))
        # the codes for the glyphs of a font with an encoding are assigned
        # by the backend document, which is recreated for each rendering pass
        if not shaper.font.encoding:
            self._segments = segments
        return segments

    def advance(self, total, space_width):
        """Add the glyph widths to `total` one by one, setting spaces at
        `space_width`"""
        for width in self.widths:
            total += space_width if width is None else width
        return total


EMPTY = ShapedString(None, '')


class TabSpace(object):
    """The space a tab takes up in a line, up to the next tab stop

    It is filled with the tab stop's fill string, if any.

    """

    nspaces = 0
    ends_with_space = False

    def __init__(self, shaper, width, tab_stop):
        self.shaper = shaper
        self.width = width
        self.tab_stop = tab_stop

    @property
    def string(self):
        return ''.join(str(char) for _, _, char in self._glyphs())

    def _glyphs(self):
        """(glyph, width, chars) for the tab and its fill"""
        shaper = self.shaper
        tab = (shaper.space_glyph, self.width, '\t')
        fill = self.tab_stop.fill
        if not fill:
            return [tab]
        fill_glyphs = list(zip(*shaper.glyphs(fill)))
        number, rest = divmod(self.width, sum(width for _, width, _
                                              in fill_glyphs))
        return [(shaper.space_glyph, rest, '\t')] + fill_glyphs * int(number)

    def segments(self, canvas, document):
        shaper = self.shaper
        glyphs = ((glyph, width) for glyph, width, _ in self._glyphs())
        return [''.join(canvas.encode_glyphs(document, shaper.font,
                                             shaper.size, glyphs))]

    def advance(self, total, space_width):
        for _, width, _ in self._glyphs():
            total += width
        return total


FALLBACK_STYLE = '_fallback_'


def handle_missing_glyphs(span, container):
    """Split off the characters missing from the span's font

    These are set in the fallback style instead.

    Yields:
        (span, TextMetrics): the (split) spans and their metrics; for inline
            flowables, the metrics are `None`

    """
    if isinstance(span, InlineFlowable):
        yield span, None
        return

    def annotate(styled_text):
        if isinstance(span, AnnotatedSpan):
            return AnnotatedSpan(styled_text, anchor=span.anchor_annotation,
                                 link=span.link_annotation)
        else:
            return styled_text

    def split_off(text):
        styled_text = annotate(SingleStyledText(text, parent=span))
        return styled_text, text_metrics(styled_text, container)

    metrics = text_metrics(span, container)
    get_glyph = metrics.shaper.glyph
    string = []
    has_missing_glyphs = False
    for char in span.text(container):
        try:
            if char not in '\n\t\N{ZERO WIDTH SPACE}\N{NO-BREAK SPACE}':
                get_glyph(char)
            string.append(char)
        except MissingGlyphException:
            has_missing_glyphs = True
            if string:
                yield split_off(''.join(string))
                string.clear()
            if span.parent.style is FALLBACK_STYLE:
                yield split_off('?')
            else:
                fallback_span = SingleStyledText(char, style=FALLBACK_STYLE, parent=span)
                yield from handle_missing_glyphs(annotate(fallback_span), container)
    if not has_missing_glyphs:
        yield span, metrics
        return
    if string:
        yield split_off(''.join(string))


# The kinds of items making up a paragraph's text (see spans_to_words)
WORD, SPACE, TAB, NEWLINE, ZERO_WIDTH_SPACE, SLASH = range(6)

Item = namedtuple('Item', 'kind width glyph_spans')
Item.__doc__ = """A word, space or other special character in a paragraph

Args:
    kind: :data:`WORD`, :data:`SPACE`, :data:`TAB`, :data:`NEWLINE` or
        :data:`ZERO_WIDTH_SPACE`
    width (float): the item's width
    glyph_spans (tuple): (span, metrics, shaped) for each of the spans making
        up the item, with `shaped` a :class:`ShapedString`, or `None` for an
        inline flowable (`span` is then its :class:`InlineFlowableSpan`)

"""

SPECIAL_CHARACTERS = {
    ' ': SPACE,
    '\t': TAB,
    '\n': NEWLINE,
    '\N{ZERO WIDTH SPACE}': ZERO_WIDTH_SPACE,
    '/': SLASH,
}

# runs of the same special character, or of regular characters
CHARACTER_RUNS = re.compile('|'.join(['{}+'.format(re.escape(char))
                                      for char in SPECIAL_CHARACTERS]
                                     + ['[^{}]+'.format(''.join(
                                         SPECIAL_CHARACTERS))]))


class DefaultTabStops(object):
    def __init__(self, tab_width):
        self.tab_width = tab_width

    def __iter__(self):
        return (TabStop(i * self.tab_width) for i in count(1))


class ParagraphState(FlowableState):
    """The position of the next word to typeset in a paragraph's words

    Args:
        index (int): index of the next word in the paragraph's words
        first_word (Item): the remainder of a hyphenated word, to typeset
            before the word at `index`

    """

    def __init__(self, paragraph, index=0, first_word=None, _initial=True):
        super().__init__(paragraph, _initial)
        self.index = index
        self.first_word = first_word

    paragraph = ReadAliasAttribute('flowable')

    def __copy__(self):
        return self.__class__(self.paragraph, self.index, self.first_word,
                              _initial=self.initial)


def spans_to_words(spans, container):
    """Split `spans` into words, spaces and other special characters

    Args:
        spans: (span, metrics) tuples, as yielded by `handle_missing_glyphs`

    Yields:
        Item: the words, spaces and other special characters

    """
    language = container.document.language
    word = []       # [span, metrics, string] for each span making up the word
    for span, metrics in spans:
        if metrics is None:     # inline flowable
            inline = span.flow_inline(container, 0)
            word.append([inline, inline.metrics, None])
            continue
        no_break_after = span.get_style('no_break_after', container)
        if no_break_after == LANGUAGE_DEFAULT:
            no_break_after = language.no_break_after
        text = span.text(container)
        if not text and getattr(span, 'anchor_annotation', None):
            word.append([span, metrics, ''])   # place the anchor
        for chars in CHARACTER_RUNS.findall(text):
            special = SPECIAL_CHARACTERS.get(chars[0])
            if special == SLASH:
                if word:
                    yield word_item(word)
                word = []
            elif special is not None:
                if not (special == SPACE
                        and last_word(word).lower() in no_break_after):
                    if word:
                        yield word_item(word)
                    item = special_item(special, span, metrics)
                    for _ in chars:
                        yield item
                    word = []
                    continue
            part = chars.replace('\N{NO-BREAK SPACE}', ' ')
            if word and word[-1][0] is span:
                word[-1][2] += part
            else:
                word.append([span, metrics, part])
    if word:
        yield word_item(word)


def word_item(word):
    """Create a word :class:`Item` from [span, metrics, string] lists"""
    glyph_spans = tuple((span, metrics, None if string is None
                         else metrics.shaper.shape(string))
                        for span, metrics, string in word)
    width = sum(span.width if shaped is None else shaped.width
                for span, _, shaped in glyph_spans)
    return Item(WORD, width, glyph_spans)


def special_item(kind, span, metrics):
    if kind == SPACE:
        space = metrics.shaper.space
        return Item(SPACE, space.width, ((span, metrics, space), ))
    return Item(kind, 0, ((span, metrics, EMPTY), ))


def last_word(word):
    """The last whitespace-separated word in `word`"""
    word_string = ''.join(str(span) if string is None else string
                          for span, _, string in word).strip()
    return word_string.rsplit(maxsplit=1)[-1] if word_string else ''


def break_lines(words, index, first_word, width, indent, tab_stops,
                significant_whitespace, container):
    """Break `words` into lines of `width` (greedy first fit)

    The word that doesn't fit on a line is hyphenated if possible. Otherwise,
    it moves to the next line, unless it is the line's first word.

    Args:
        words (list): the paragraph's words, spaces and special characters
            (:class:`Item`)
        index (int): index of the first word to typeset
        first_word (Item): typeset before `words[index]` (the remainder of
            a hyphenated word), or `None`
        indent (float): left indent of the first line
        container (Container): used for looking up styles only

    Yields:
        (Line, bool, range, tuple): each line, whether it is a paragraph's last
        line or ended by a newline character, the indices of the words that
        were looked at when building it (the last one is `len(words)` at the
        end of the paragraph) and the (index, first_word) position following
        the line. The final line is empty when the paragraph's last line was
        ended by a newline character, or when there are no words.

    """
    wrapped = continued = False
    while True:
        line = Line(tab_stops, width, indent, significant_whitespace,
                    continued)
        indent = 0
        start = end = index
        while True:
            if first_word:
                word, first_word = first_word, None
            elif index < len(words):
                word = words[index]
                index = end = index + 1
            else:   # end of paragraph
                yield line, True, range(start, index + 1), (index, None)
                return
            if word.kind == NEWLINE:
                if not wrapped:     # ignore newlines directly after a wrap
                    line.extend(word.glyph_spans)
                    break
            elif line.append_word(word):
                wrapped = False
            else:
                wrapped = True
                for first, second, is_last in hyphenate(word, container):
                    if line.append_word(first, force=is_last):
                        first_word = second
                        break
                else:   # three possibilities:
                        # - shortest hyphenated part of the word doesn't fit
                        # - word cannot be hyphenated
                        # - hyphenation is off
                    if not line:    # first word on line, so typeset it anyway
                        line.append_word(word, True)
                    else:           # move the word to the next line
                        index -= 1
                break
        yield line, not wrapped, range(start, end), (index, first_word)
        continued = wrapped


def has_inline_flowables(words):
    return any(shaped is None
               for word in words for _, _, shaped in word.glyph_spans)


class ParagraphBase(Flowable, Label):
    """Base class for paragraphs

    A paragraph holds styled text and other line elements to be flowed into a
    container.

    """

    category = 'paragraph'
    style_class = ParagraphStyle
    significant_whitespace = False

    def __init__(self, custom_label=None, align=None, width=None,
                 id=None, style=None, parent=None, source=None):
        super().__init__(align=align, width=width,
                         id=id, style=style, parent=parent, source=source)
        Label.__init__(self, custom_label=custom_label)

    @property
    def referenceable(self):
        return self

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        document = flowable_target.document
        number_format = self.get_style('number_format', flowable_target)
        if self.get_style('custom_label', flowable_target):
            assert self.custom_label is not None
            label = str(self.custom_label)
        elif number_format:
            numbering_level = self.get_style('numbering_level', flowable_target)
            section = self.section
            if numbering_level < 0:
                numbering_level = section.level + numbering_level
            while section and section.level > numbering_level:
                section = section.parent.section
            section_id = section.get_id(document, False) if section else None
            ref_category = self.referenceable.category
            section_counters = document.counters.setdefault(ref_category, {})
            section_counter = section_counters.setdefault(section_id, [])
            section_counter.append(self)
            number = len(section_counter)
            label = self.prepare_label(number, section, flowable_target)
        else:
            return
        category_label = StringField(self.referenceable.category)
        reference = MixedStyledText([category_label, ' ', label])
        for id in self.referenceable.get_ids(document):
            document.set_reference(id, 'number', label)
            document.set_reference(id, 'reference', reference)

    def prepare_label(self, number, parent_section, container):
        document = container.document
        number_format = self.get_style('number_format', container)
        label = format_number(number, number_format)
        separator = self.get_style('number_separator', container)
        if separator is not None and parent_section and parent_section.level > 0:
            parent_id = parent_section.get_id(document)
            parent_ref = document.get_reference(parent_id, 'number', None)
            if parent_ref:
                separator_string = separator.to_string(container)
                label = copy(parent_ref) + separator_string + label
        return label

    def number(self, container):
        document = container.document
        target_id = self.referenceable.get_id(document)
        formatted_number = document.get_reference(target_id, 'number')
        if formatted_number:
            label = self.format_label(formatted_number, container)
            label.style = 'label'
            return label
        else:
            return ''

    def text(self, container):
        text = []
        if self.get_style('number_format', container):
            text.append(self.number(container))
        before = self.get_style('before', container)
        if before is not None:
            text.append(before.copy())
        text.append(self.content)
        after = self.get_style('after', container)
        if after is not None:
            text.append(after.copy())
        return MixedStyledText(text, parent=self)

    @property
    def paragraph(self):
        return self

    def initial_state(self, container):
        return ParagraphState(self)

    def words(self, container):
        """The words making up this paragraph's text

        Returns:
            (list, list): the words, and for each word (plus one for the end
            of the paragraph), the styled text items to register with the
            container (style log, :meth:`before_placing`) when consuming it

        The words are cached, so that they are not recreated each time the
        paragraph is rendered (e.g. to measure it). The cache is valid for the
        current document part rendering pass, or for the current page only
        when the text contains page-dependent fields (e.g. the page number).
        Inline flowables are flowed into a virtual container that is placed
        later, so these need to be created for each rendering.

        """
        page, document_part = container.page, container.document_part
        cache = container.document.paragraph_words
        try:
            key, words_and_registrations = cache[self]
            if key is document_part or key is page:
                return words_and_registrations
        except KeyError:
            pass
        # the styled text items are registered with the container while
        # iterating over the spans; take them back out and keep track of
        # which word caused them to be registered
        registered = container.registered_styleds()
        start = len(registered)
        spans = self.text(container).wrapped_spans(container)
        fixed_spans = (fixed_span for span in spans
                       for fixed_span in handle_missing_glyphs(span, container))
        words, registrations = [], []
        for word in spans_to_words(fixed_spans, container):
            words.append(word)
            registrations.append(registered[start:])
            del registered[start:]
        registrations.append(registered[start:])
        del registered[start:]
        words_and_registrations = words, registrations
        if not has_inline_flowables(words):
            depends_on_page = any(getattr(styled, 'depends_on_page', False)
                                  for styleds in registrations
                                  for styled, _ in styleds)
            key = page if depends_on_page else document_part
            cache[self] = key, words_and_registrations
        return words_and_registrations

    def _short_repr_args(self, flowable_target):
        yield self._short_repr_string(flowable_target)

    def to_string(self, flowable_target):
        return ''.join(item.to_string(flowable_target) for
                       item in self.text(flowable_target))

    def _text(self, container):
        raise NotImplementedError('{}.text()'.format(self.__class__.__name__))

    def _tab_stops(self, container):
        tab_stops = self.get_style('tab_stops', container)
        if not tab_stops:
            tab_width = 2 * self.get_style('font_size', container)
            tab_stops = DefaultTabStops(tab_width)
        return tab_stops

    def content_width(self, width, container):
        if type(self).render is not ParagraphBase.render:
            return None
        words, _ = self.words(container)
        if has_inline_flowables(words):
            return None     # their size can depend on the container width
        indent_first = float(self.get_style('indent_first', container))
        lines = break_lines(words, 0, None, float(width), indent_first,
                            self._tab_stops(container),
                            self.significant_whitespace, container)
        return max([0, *(line.cursor for line, *_ in lines if line)])

    def render(self, container, descender, state, space_below=0,
               first_line_only=False):
        """Typeset the paragraph

        The paragraph is typeset in the given container starting below the
        current cursor position of the container. When the end of the container
        is reached, the rendering state is preserved to continue setting the
        rest of the paragraph when this method is called with a new container.

        Args:
            container (Container): the container to render to
            descender (float or None): descender height of the preceding line
            state (ParagraphState): the state where rendering will continue
            first_line_only (bool): typeset only the first line

        """
        indent_first = (float(self.get_style('indent_first', container))
                        if state.initial else 0)
        line_width = float(container.width)
        line_spacing = self.get_style('line_spacing', container)
        text_align = self.get_style('text_align', container)
        tab_stops = self._tab_stops(container)
        split_minimum_lines = self.get_style('split_minimum_lines', container)
        words, registrations = self.words(container)

        initial_state = copy(state)
        # `saved_state` is updated after successfully rendering each line, so
        # that when `container` overflows on rendering a line, the words in that
        # line are typeset again on the next render() call.
        saved_state = initial_state
        max_line_width = 0
        lines_typeset = 0
        first_line_advance = 0
        lines = break_lines(words, state.index, state.first_word, line_width,
                            indent_first, tab_stops,
                            self.significant_whitespace, container)
        for line, last_line, words_seen, (index, first_word) in lines:
            # register the styled text items making up the line's words with
            # the container (style log, before_placing)
            for word_index in words_seen:
                for styled, continued in registrations[word_index]:
                    container.register_styled(styled, continued)
            for span, message in line.warnings:
                span.warn(message, container)
            if not line:
                break
            max_line_width = max(max_line_width, line.cursor)
            # descender is None when this is the first line in the container
            advance = (line.ascender if descender is None
                       else line_spacing.advance(line, descender, container))
            descender = line.descender   # descender <= 0
            if not lines_typeset:
                first_line_advance = advance
            total_advance = (advance + (space_below if last_line else 0)
                             - descender)
            if container.remaining_height < total_advance:
                if lines_typeset < split_minimum_lines:
                    raise EndOfContainer(initial_state)
                raise EndOfContainer(saved_state)
            assert container.advance2(advance)
            try:
                line.typeset(container, text_align, last_line)
            except ContainerOverflow:
                raise EndOfContainer(saved_state)
            assert container.advance2(- descender)
            state.index, state.first_word = index, first_word
            state.initial = False
            lines_typeset += 1
            saved_state = copy(state)
            if first_line_only:
                break

        # Correct the horizontal text placement for auto-width paragraphs
        if self._width(container) == FlowableWidth.AUTO:
            if text_align == TextAlign.CENTER:
                container.left -= float(container.width - max_line_width) / 2
            if text_align == TextAlign.RIGHT:
                container.left -= float(container.width - max_line_width)

        return max_line_width, first_line_advance, descender


class StaticParagraph(ParagraphBase):
    """A paragraph of static text

    Args:
        content (StyledText): the paragraph's text content

    """
    has_title = False

    def __init__(self, content, custom_label=None, align=None, width=None,
                 id=None, style=None, parent=None, source=None):
        super().__init__(custom_label=custom_label, align=align, width=width,
                         id=id, style=style, parent=parent, source=source)
        if isinstance(content, str):
            content = SingleStyledText(content)
        elif isinstance(content, Iterable):
            content = MixedStyledText(content)
        assert content.parent is None
        content.parent = self
        self.content = content

    def prepare(self, container):
        super().prepare(container)
        self.content.prepare(container)
        if self.has_title:
            for id in self.referenceable.get_ids(container.document):
                container.document.set_reference(id, 'title', self.content)

    def _text(self, container):
        return self.content


class Paragraph(StaticParagraph):
    pass


class HyphenatorStore(dict):
    def __missing__(self, key):
        hyphen_lang, hyphen_chars = key
        dic_path = dic_file = 'hyph_{}.dic'.format(hyphen_lang)
        if not path.exists(dic_path):
            dic_path = path.join(path.join(DATA_PATH, 'hyphen'), dic_file)
            if not path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))
        self[key] = Hyphenator(dic_path, hyphen_chars, hyphen_chars)
        return self[key]


HYPHENATORS = HyphenatorStore()


def create_hyphenate(span, container):
    if not span.get_style('hyphenate', container):
        def dont_hyphenate(word):
            return
            yield
        return dont_hyphenate

    hyphenator = HYPHENATORS[span.get_style('hyphen_lang', container),
                             span.get_style('hyphen_chars', container)]
    def hyphenate(word):
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
        for first, second, is_last in hyphenator.iterate(word):
            yield first + '-', second, is_last
    return hyphenate


def hyphenate(word, container):
    """Yield the ways to split `word` (:class:`Item`) across two lines

    Yields:
        (Item, Item, bool): the first part (with trailing hyphen), the second
        part and whether this is the last option. In the first option, the
        word is split at the right-most possible break point. In subsequent
        options, the break point advances to the front of the word.

    """
    # TODO: hyphenate mixed-styled words (if lang is the same)
    if word.kind != WORD or len(word.glyph_spans) > 1:
        return
    (span, metrics, shaped), = word.glyph_spans
    if shaped is None:      # inline flowable
        return
    hyphenate_word = create_hyphenate(span, container)
    words = shaped.string.split()
    for i, word in enumerate(words):
        for first, second, is_last in hyphenate_word(word):
            first_part = ' '.join(chain(words[:i], [first]))
            second_part = ' '.join(chain([second], words[i+1:]))
            yield (word_item([[span, metrics, first_part]]),
                   word_item([[span, metrics, second_part]]), is_last)


class Line(list):
    """Helper class for building and typesetting a single line of text within
    a paragraph.

    Holds a (span, metrics, shaped) glyph span for each span making up the
    line's items (see :class:`Item`).

    Args:
        tab_stops (TabStopList): as given in the paragraph style
        width (float): the available line width
        indent (float): left indent width (positive or negative)
        significant_whitespace (bool): whether to typeset whitespace as-is or
            consider them as tokens separating words
        continued (bool): whether this line is a continuation of a previous line
            (in which case whitespace at the start of the line is dropped)

    """

    def __init__(self, tab_stops, width, indent=0,
                 significant_whitespace=False, continued=False):
        super().__init__()
        self.tab_stops = tab_stops
        self.width = width
        self.indent = indent
        self.cursor = indent
        self.advance = 0
        self.significant_whitespace = significant_whitespace
        self.wrapped_line = continued
        self._current_tab = None
        self.warnings = []      # (span, message) tuples

    def __str__(self):
        return ''.join(str(span) if shaped is None else shaped.string
                       for span, _, shaped in self)

    def __repr__(self):
        return f"{type(self).__name__}('{self}')"

    def _handle_tab(self, span, metrics):
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self.cursor < tab_position:
                tab = TabSpace(metrics.shaper, tab_position - self.cursor,
                               tab_stop)
                self.append((span, metrics, tab))
                self.cursor = tab_position
                if tab_stop.align in (TabAlign.RIGHT, TabAlign.CENTER):
                    self._current_tab = tab
                else:
                    self._current_tab = None
                break
        else:
            self.append((span, metrics, EMPTY))
            self.warnings.append((span, 'Tab did not fall into any of the '
                                        'tab stops.'))

    def append_word(self, item, force=False):
        kind = item.kind
        if kind == SPACE:
            if not self and (not self.significant_whitespace
                             or self.wrapped_line):
                return True
        elif kind == TAB:
            (span, metrics, _), = item.glyph_spans
            self._handle_tab(span, metrics)
            return True
        width = item.width
        if self._current_tab:
            current_tab = self._current_tab
            tab_width = current_tab.width
            factor = (2 if current_tab.tab_stop.align == TabAlign.CENTER
                      else 1)
            item_width = width / factor
            if item_width < tab_width:
                current_tab.width -= item_width
            else:
                self.warnings.append((item.glyph_spans[0][0],
                                      'Tab space exceeded.'))
                current_tab.width = 0
                self._current_tab = None
            self.cursor -= item_width
        if self.cursor + width > self.width:
            if self or not force:
                return False
            elif self.width > 0:
                self.warnings.append((item.glyph_spans[0][0],
                                      'item too long to fit on line'))
        self.cursor += width
        self.extend(item.glyph_spans)
        return True

    @property
    def ascender(self):
        return max(metrics.ascender for _, metrics, _ in self)

    @property
    def descender(self):
        return min(metrics.descender for _, metrics, _ in self)

    @property
    def height(self):
        return max(metrics.height for _, metrics, _ in self)

    @property
    def line_gap(self):
        return max(metrics.line_gap for _, metrics, _ in self)

    def typeset(self, container, text_align, last_line=False):
        """Typeset the line in `container` below its current cursor position.
        Advances the container's cursor to below the descender of this line.

        `justification` and `line_spacing` are passed on from the paragraph
        style. `last_descender` is the previous line's descender, used in the
        vertical positioning of this line. Finally, `last_line` specifies
        whether this is the last line of the paragraph.

        Returns the line's descender size."""
        # drop spaces (and empty spans) at the end of the line
        while len(self) > 0:
            _, metrics, shaped = self[-1]
            if shaped is not None and shaped.ends_with_space:
                self.cursor -= metrics.shaper.space_width
                self.pop()
            else:
                break
        else:   # abort if the line is empty
            return

        if container.never_placed:      # only measuring; no need to draw
            return

        descender = self.descender
        # Temporarily advance with descender so that overflow on
        # before_placing (e.g. footnotes) can be detected
        assert container.advance2(- descender)
        for span, _, _ in self:
            span.before_placing(container, preallocate=True)
        assert container.advance2(descender)

        # horizontal displacement
        left = self.indent

        if self._current_tab or text_align == TextAlign.JUSTIFY and last_line:
            text_align = 'left'
        extra_space = self.width - self.cursor
        add_to_spaces = None
        if text_align == TextAlign.JUSTIFY:
            # TODO: padding added to spaces should be prop. to font size
            nr_spaces = sum(shaped.nspaces for _, _, shaped in self
                            if shaped is not None)
            if nr_spaces > 0:
                add_to_spaces = extra_space / nr_spaces
        elif text_align == TextAlign.CENTER:
            left += extra_space / 2.0
        elif text_align == TextAlign.RIGHT:
            left += extra_space

        document = container.document
        canvas = container.canvas
        cursor = container.cursor
        current_annotation = AnnotationState(container)
        for span, metrics, shapeds in group_spans(self):
            if shapeds is None:      # inline flowable
                if metrics.ascender > 0:
                    top = cursor - metrics.ascender
                else:
                    inline_height = span.virtual_container.height
                    top = cursor - metrics.descender - inline_height
                span.virtual_container.place_at(container, left, top)
                width = span.width
            else:
                width = show_text(canvas, left, cursor, metrics, shapeds,
                                  add_to_spaces, document)
            current_annotation.update(span, metrics, left, width)
            left += width
        current_annotation.place_if_any()


def show_text(canvas, left, cursor, metrics, shapeds, add_to_spaces,
              document):
    """Show the shaped strings set in the same span

    Args:
        shapeds (list): the span's :class:`ShapedString`s (and
            :class:`TabSpace`s) in the line
        add_to_spaces (float): extra width for each space (justification), or
            `None`

    Returns:
        float: the width of the shown text

    """
    shaper = metrics.shaper
    # encode the glyphs in order; the backend can assign glyph codes
    segments = [shaped.segments(canvas, document) for shaped in shapeds]
    space_width = shaper.space_width
    if add_to_spaces is not None:
        space_width += add_to_spaces
    space = ''
    if any(shaped.nspaces for shaped in shapeds):
        space, = canvas.encode_glyphs(document, shaper.font, shaper.size,
                                      [(shaper.space_glyph, space_width)])
    canvas.show_glyphs(left, cursor, metrics,
                       ''.join(space.join(segs) for segs in segments),
                       document)
    width = 0
    for shaped in shapeds:
        width = shaped.advance(width, space_width)
    return width


def group_spans(line):
    """Group consecutive glyphs spans belonging to the same span

    Yields:
        (span, metrics, shapeds): the shaped strings set in `span`; `shapeds`
            is `None` for an inline flowable

    """
    span = None
    for glyph_span, glyph_metrics, shaped in line:
        if shaped is None:      # inline flowable
            if span:
                yield span, metrics, shapeds
            yield glyph_span, glyph_metrics, None
            span = None
        elif glyph_span is not span:
            if span:
                yield span, metrics, shapeds
            span, metrics, shapeds = glyph_span, glyph_metrics, [shaped]
        else:
            shapeds.append(shaped)
    if span:
        yield span, metrics, shapeds


class AnnotationRect(object):
    __slots__ = ('annotation', 'left', 'width', 'height', 'ascender')

    def __init__(self, annotation, left, width, height, ascender):
        self.annotation = annotation
        self.left = left
        self.width = width
        self.height = height
        self.ascender = ascender

    def update(self, width, height, ascender):
        self.width += width
        self.height = max(self.height, height)
        self.ascender = max(self.ascender, ascender)


class AnnotationState(object):
    __slots__ = ('anchor', 'link', 'container')

    def __init__(self, container):
        self.anchor = None
        self.link = None
        self.container = container

    def update_annotation(self, span, metrics, annotation_type, left, width):
        annotation = getattr(span, annotation_type + '_annotation')
        annotation_rect = getattr(self, annotation_type)
        if annotation_rect and annotation is not annotation_rect.annotation:
            self.place_if_any(annotation_type)
        if annotation:
            if annotation_rect and annotation is annotation_rect.annotation:
                annotation_rect.update(width, metrics.height,
                                       metrics.ascender)
            else:
                annotation_rect = AnnotationRect(annotation, left, width,
                                                 metrics.height,
                                                 metrics.ascender)
        else:
            annotation_rect = None
        setattr(self, annotation_type, annotation_rect)

    def update(self, span, metrics, left, width):
        if isinstance(span, AnnotatedSpan):
            self.update_annotation(span, metrics, 'anchor', left, width)
            self.update_annotation(span, metrics, 'link', left, width)

    def place_if_any(self, annotation_type=None):
        annotation_types = ((annotation_type, ) if annotation_type
                            else ('anchor', 'link'))
        for type in annotation_types:
            annotation_rect = getattr(self, type)
            if annotation_rect:
                top = self.container.cursor - annotation_rect.ascender
                self.container.canvas.annotate(annotation_rect.annotation,
                                               annotation_rect.left, top,
                                               annotation_rect.width,
                                               annotation_rect.height)
