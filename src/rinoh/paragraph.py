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
from copy import copy
from functools import partial
from itertools import tee, chain, groupby, count
from os import path

from . import DATA_PATH
from .annotation import AnnotatedSpan
from .attribute import (Attribute, AttributeType, OptionSet, ParseError,
                        OverrideDefault)
from .dimension import Dimension, PT
from .flowable import Flowable, FlowableStyle, FlowableState, FlowableWidth
from .font import MissingGlyphException
from .hyphenator import Hyphenator
from .inline import InlineFlowableException
from .layout import EndOfContainer, ContainerOverflow
from .text import TextStyle, MixedStyledText, SingleStyledText, ESCAPE
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
        max_line_gap = max(float(glyph_span.span.line_gap(container))
                           for glyph_span in line)
        max_ascender = max(float(glyph_span.span.ascender(container))
                           for glyph_span in line)
        return max_ascender + max_line_gap


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
        max_font_size = max(float(glyph_span.span.height(container))
                            for glyph_span in line)
        return self.factor * max_font_size + last_descender


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
        document = container
        max_ascender = max(float(item.span.ascender(document)) for item in line)
        return max_ascender + float(self.leading)


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
            positon
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
class ParagraphStyle(FlowableStyle, TextStyle):
    width = OverrideDefault('fill')

    indent_first = Attribute(Dimension, 0*PT, 'Indentation of the first line '
                                              'of text')
    line_spacing = Attribute(LineSpacing, DEFAULT, 'Spacing between the '
                             'baselines of two successive lines of text')
    text_align = Attribute(TextAlign, 'justify', 'Alignment of text to the '
                                                 'margins')
    tab_stops = Attribute(TabStopList, TabStopList(), 'List of tab positions')


class Glyph(object):
    __slots__ = ('glyph', 'width', 'char')

    def __init__(self, glyph, width, char):
        self.glyph = glyph
        self.width = width
        self.char = char


def form_ligatures(chars_and_glyphs, get_ligature):
    prev_char, prev_glyph = next(chars_and_glyphs)
    for char, glyph in chars_and_glyphs:
        ligature_glyph = get_ligature(prev_glyph, glyph)
        if ligature_glyph:
            prev_char += char
            prev_glyph = ligature_glyph
        else:
            yield prev_char, prev_glyph
            prev_char, prev_glyph = char, glyph
    yield prev_char, prev_glyph


def kern(chars_and_glyphs, get_kerning):
    prev_char, prev_glyph = next(chars_and_glyphs)
    for char, glyph in chars_and_glyphs:
        yield prev_char, prev_glyph, get_kerning(prev_glyph, glyph)
        prev_char, prev_glyph = char, glyph
    yield prev_char, prev_glyph, 0.0


def create_lig_kern(span, flowable_target):
    font = span.font(flowable_target)
    scale = span.height(flowable_target) / font.units_per_em
    variant = span.get_style('font_variant', flowable_target)
    kerning = span.get_style('kerning', flowable_target)
    ligatures = span.get_style('ligatures', flowable_target)
    get_glyph = partial(font.get_glyph, variant=variant)
    # TODO: handle ligatures at span borders
    def lig_kern(chars, glyphs=None):
        if glyphs is None:
            glyphs = (get_glyph(char) for char in chars)
        chars_and_glyphs = zip(chars, glyphs)
        if ligatures:
            chars_and_glyphs = form_ligatures(chars_and_glyphs,
                                              font.get_ligature)
        if kerning:
            glyphs_kern = kern(chars_and_glyphs, font.get_kerning)
        else:
            glyphs_kern = [(char, glyph, 0.0)
                           for char, glyph in chars_and_glyphs]
        return [Glyph(glyph, scale * (glyph.width + kern_adjust), char)
                for char, glyph, kern_adjust in glyphs_kern]

    return get_glyph, lig_kern


def handle_missing_glyphs(span, container):
    get_glyph, _ = create_lig_kern(span, container)
    string = []
    for char in span.text(container):
        try:
            get_glyph(char)
            string.append(char)
        except MissingGlyphException:
            if string:
                yield SingleStyledText(''.join(string), parent=span)
                string.clear()
            if span.parent.style == '_fallback_':
                yield SingleStyledText('?', parent=span)
            else:
                yield SingleStyledText(char, style='_fallback_', parent=span)
    if string:
        yield SingleStyledText(''.join(string), parent=span)


class LinePart(object):
    pass


class SpecialCharacter(LinePart):
    def __init__(self, span, chars_to_glyphs):
        self.glyphs_span = GlyphsSpan(span, chars_to_glyphs)

    def __iter__(self):
        yield self.glyphs_span

    @property
    def width(self):
        return self.glyphs_span.width


class Space(SpecialCharacter):
    char = ' '

    def __init__(self, span, chars_to_glyphs):
        super().__init__(span, chars_to_glyphs)
        self.glyphs_span.append_space()

    def hyphenate(self, container):
        return iter([])

    def __getitem__(self, index):
        raise SpaceException


class SpaceException(Exception):
    pass


class Tab(SpecialCharacter):
    char = '\t'

    def __getitem__(self, index):
        raise TabException


class TabException(Exception):
    pass


class NewLine(SpecialCharacter):
    char = '\n'

    def __getitem__(self, index):
        raise NewLineException


class NewLineException(Exception):
    pass


class ZeroWidthSpace(SpecialCharacter):
    char = '\N{ZERO WIDTH SPACE}'

    def __getitem__(self, index):
        assert index == 0
        return self.glyphs_span


WHITESPACE = {' ': Space,
              '\t': Tab,
              '\n': NewLine,
              '\N{ZERO WIDTH SPACE}': ZeroWidthSpace}


# TODO: shouldn't take a container (but needed by flow_inline)
# (return InlineFlowableSpan that raises InlineFlowableException later)
def spans_to_words(spans, container):
    word = Word()
    spans = iter(spans)
    while True:
        try:
            span = next(spans)
        except StopIteration:
            break
        try:
            get_glyph, lig_kern = create_lig_kern(span, container)
            groups = groupby(iter(span.text(container)), WHITESPACE.get)
            for special, characters in groups:
                if special:
                    if word:
                        yield word
                    for _ in characters:
                        yield special(span, lig_kern)
                    word = Word()
                else:
                    part = ''.join(characters)
                    try:
                        glyphs = [get_glyph(char) for char in part]
                    except MissingGlyphException:
                        rest = ''.join(char for _, group in groups
                                       for char in group)
                        rest_of_span = SingleStyledText(part + rest,
                                                        parent=span)
                        new_spans = handle_missing_glyphs(rest_of_span,
                                                          container)
                        spans = chain(new_spans, spans)
                        break
                    glyphs_and_widths = lig_kern(part, glyphs)
                    glyphs_span = GlyphsSpan(span, lig_kern, glyphs_and_widths)
                    word.append(glyphs_span)
        except InlineFlowableException:
            glyphs_span = span.flow_inline(container, 0)
            word.append(glyphs_span)
    if word:
        yield word


class DefaultTabStops(object):
    def __init__(self, tab_width):
        self.tab_width = tab_width

    def __iter__(self):
        return (TabStop(i * self.tab_width) for i in count(1))


class ParagraphState(FlowableState):
    def __init__(self, paragraph, words, nested_flowable_state=None,
                 _first_word=None, _initial=True):
        super().__init__(paragraph, _initial)
        self._words = words
        self.nested_flowable_state = nested_flowable_state
        self._first_word = _first_word

    paragraph = ReadAliasAttribute('flowable')

    def __copy__(self):
        copy_words, self._words = tee(self._words)
        copy_nested_flowable_state = copy(self.nested_flowable_state)
        return self.__class__(self.paragraph, copy_words,
                              copy_nested_flowable_state,
                              _first_word=self._first_word,
                              _initial=self.initial)

    def next_word(self):
        if self._first_word:
            word = self._first_word
            self._first_word = None
        else:
            word = next(self._words)
        return word

    def prepend_word(self, word):
        self._first_word = word


class ParagraphBase(Flowable):
    """Base class for paragraphs

    A paragraph is a collection of mixed-styled text that can be flowed into a
    container.

    """

    style_class = ParagraphStyle
    significant_whitespace = False

    @property
    def paragraph(self):
        return self

    def initial_state(self, container):
        spans = self.text(container).wrapped_spans(container)
        return ParagraphState(self, spans_to_words(spans, container))

    def _short_repr_args(self, flowable_target):
        yield self._short_repr_string(flowable_target)

    def to_string(self, flowable_target):
        return ''.join(item.to_string(flowable_target) for
                       item in self.text(flowable_target))

    def text(self, container):
        raise NotImplementedError('{}.text()'.format(self.__class__.__name__))

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
        tab_stops = self.get_style('tab_stops', container)
        if not tab_stops:
            tab_width = 2 * self.get_style('font_size', container)
            tab_stops = DefaultTabStops(tab_width)

        # `saved_state` is updated after successfully rendering each line, so
        # that when `container` overflows on rendering a line, the words in that
        # line are yielded again on the next typeset() call.
        saved_state = copy(state)
        prev_state = copy(state)
        max_line_width = 0

        def typeset_line(line, last_line=False):
            """Typeset `line` and, if no exception is raised, update the
            paragraph's internal rendering state.

            Args:
                line (Line): the line to typeset
                last_line (bool): True if this is the paragraph's last line

            """
            nonlocal state, saved_state, max_line_width, descender, space_below
            max_line_width = max(max_line_width, line.cursor)
            # descender is None when this is the first line in the container
            advance = (line.ascender(container) if descender is None
                       else line_spacing.advance(line, descender, container))
            descender = line.descender(container)   # descender <= 0
            line.advance = advance
            total_advance = advance + (space_below if last_line else 0) - descender
            if container.remaining_height < total_advance:
                raise EndOfContainer(saved_state)
            assert container.advance2(advance)
            try:
                line.typeset(container, text_align, last_line)
            except ContainerOverflow:
                raise EndOfContainer(saved_state)
            assert container.advance2(- descender)
            state.initial = False
            saved_state = copy(state)
            return Line(tab_stops, line_width, container,
                        significant_whitespace=self.significant_whitespace)

        first_line = line = Line(tab_stops, line_width, container,
                                 indent_first, self.significant_whitespace)
        while True:
            try:
                word = state.next_word()
            except StopIteration:
                break
            try:
                if not line.append_word(word):
                    for first, second in word.hyphenate(container):
                        if line.append_word(first):
                            state.prepend_word(second)  # prepend second part
                            break
                    else:
                        state = prev_state
                    line = typeset_line(line)
                    if first_line_only:
                        break
                    continue
            except NewLineException:
                line.append(word.glyphs_span)
                line = typeset_line(line, last_line=True)
                if first_line_only:
                    break
            prev_state = copy(state)
        if line:
            typeset_line(line, last_line=True)

        # Correct the horizontal text placement for auto-width paragraphs
        if self._width(container) == FlowableWidth.AUTO:
            if text_align == TextAlign.CENTER:
                container.left -= float(container.width - max_line_width) / 2
            if text_align == TextAlign.RIGHT:
                container.left -= float(container.width - max_line_width)

        return max_line_width, first_line.advance, descender


class Paragraph(MixedStyledText, ParagraphBase):
    """A paragraph of static text

    Args:
        text_or_items: see :class:`.MixedStyledText`
        style: see :class:`.Styled`
        parent: see :class:`.DocumentElement`

    """

    style_class = ParagraphBase.style_class
    fallback_to_parent = ParagraphBase.fallback_to_parent

    def text(self, container):
        return self


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
        for first, second in hyphenator.iterate(word):
            yield first + '-', second
    return hyphenate


class GlyphsSpan(list):
    def __init__(self, span, chars_to_glyphs, glyphs_and_widths=[]):
        super().__init__()
        self.span = span
        self.filled_tabs = {}
        self.chars_to_glyphs = chars_to_glyphs
        self.space, = chars_to_glyphs(' ')
        super().__init__(glyphs_and_widths)

    def __str__(self):
        return ''.join(glyph_and_width.char for glyph_and_width in self)

    @property
    def width(self):
        return sum(glyph_and_width.width for glyph_and_width in self)

    @property
    def number_of_spaces(self):
        return self.count(self.space)

    @property
    def ends_with_space(self):
        return self[-1] == self.space

    def append_space(self):
        self.append(self.space)

    def _fill_tabs(self):
        for index, glyph_and_width in enumerate(super().__iter__()):
            if index in self.filled_tabs:
                fill_string = self.filled_tabs[index]
                fill_glyphs = self.chars_to_glyphs(fill_string)
                fill_string_width = sum(glyph.width for glyph in fill_glyphs)
                number, rest = divmod(glyph_and_width.width, fill_string_width)
                yield Glyph(glyph_and_width.glyph, rest, glyph_and_width.char)
                for i in range(int(number)):
                    for fill_glyph_and_width in fill_glyphs:
                        yield fill_glyph_and_width
            else:
                yield glyph_and_width

    def __iter__(self):
        if self.filled_tabs:
            return self._fill_tabs()
        else:
            return super().__iter__()


class Word(LinePart, list):
    def __init__(self, glyphs_spans=()):
        super().__init__(glyphs_spans)

    def __str__(self):
        return ''.join(str(glyphs_span) for glyphs_span in self)

    @property
    def width(self):
        return sum(glyph_span.width for glyph_span in self)

    def hyphenate(self, container):
        # TODO: hyphenate mixed-styled words (if lang is the same)
        if len(self) > 1:
            return
        first_glyphs_span, = self
        span = first_glyphs_span.span
        c2g = first_glyphs_span.chars_to_glyphs
        hyphenate = create_hyphenate(first_glyphs_span.span, container)
        for first, second in hyphenate(str(self)):
            first_gs = GlyphsSpan(span, c2g, c2g(first))
            second_gs = GlyphsSpan(span, c2g, c2g(second))
            yield Word([first_gs]), Word([second_gs])


class Line(list):
    """Helper class for building and typesetting a single line of text within
    a :class:`Paragraph`."""

    def __init__(self, tab_stops, width, container, indent=0,
                 significant_whitespace=False):
        """`tab_stops` is a list of tab stops, as given in the paragraph style.
        `width` is the available line width.
        `indent` specifies the left indent width.
        `container` passes the :class:`Container` that wil hold this line."""
        super().__init__()
        self.tab_stops = tab_stops
        self.width = width
        self.indent = indent
        self.container = container
        self.cursor = indent
        self.advance = 0
        self.significant_whitespace = significant_whitespace
        self._has_tab = False
        self._current_tab = None
        self._current_tab_stop = None

    def _handle_tab(self, glyphs_span):
        span = glyphs_span.span
        self._has_tab = True
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self.cursor < tab_position:
                tab_width = tab_position - self.cursor
                tab = Glyph(glyphs_span.space.glyph, tab_width, '\t')
                if tab_stop.fill:
                    glyphs_span.filled_tabs[len(glyphs_span)] = tab_stop.fill
                glyphs_span.append(tab)
                self.cursor = tab_position
                self._current_tab_stop = tab_stop
                if tab_stop.align in (TabAlign.RIGHT, TabAlign.CENTER):
                    self._current_tab = tab
                    self._current_tab_stop = tab_stop
                else:
                    self._current_tab = None
                    self._current_tab_stop = None
                break
        else:
            span.warn('Tab did not fall into any of the tab stops.',
                      self.container)

    def append_word(self, word_or_inline):
        try:
            first_glyphs_span = word_or_inline[0]
        except SpaceException:
            if not self and not self.significant_whitespace:
                return True
            first_glyphs_span = word_or_inline.glyphs_span
        except TabException:
            empty_glyphs_span = copy(word_or_inline.glyphs_span)
            self._handle_tab(empty_glyphs_span)
            self.append(empty_glyphs_span)
            return True

        width = word_or_inline.width
        if self._current_tab:
            current_tab = self._current_tab
            tab_width = current_tab.width
            factor = (2 if self._current_tab_stop.align == TabAlign.CENTER
                      else 1)
            item_width = width / factor
            if item_width < tab_width:
                current_tab.width -= item_width
            else:
                first_glyphs_span.span.warn('Tab space exceeded.',
                                            self.container)
                current_tab.width = 0
                self._current_tab = None
            self.cursor -= item_width
        if self.cursor + width > self.width:
            if self:
                return False
            elif self.width > 0:
                first_glyphs_span.span.warn('item too long to fit on line',
                                            self.container)
        self.cursor += width
        for glyphs_span in word_or_inline:
            self.append(glyphs_span)
        return True

    def descender(self, container):
        return min(glyph_span.span.descender(container) for glyph_span in self)

    def ascender(self, container):
        return max(glyph_span.span.ascender(container) for glyph_span in self)

    def typeset(self, container, text_align, last_line=False):
        """Typeset the line in `container` below its current cursor position.
        Advances the container's cursor to below the descender of this line.

        `justification` and `line_spacing` are passed on from the paragraph
        style. `last_descender` is the previous line's descender, used in the
        vertical positioning of this line. Finally, `last_line` specifies
        whether this is the last line of the paragraph.

        Returns the line's descender size."""
        document = container.document

        # drop spaces (and empty spans) at the end of the line
        while len(self) > 0:
            last_span = self[-1]
            if last_span and last_span.ends_with_space:
                self.cursor -= last_span.space.width
                self.pop()
            else:
                break
        else:   # abort if the line is empty
            return

        descender = self.descender(container)
        # Temporarily advance with descender so that overflow on
        # before_placing (e.g. footnotes) can be detected
        assert container.advance2(- descender)
        for glyph_span in self:
            glyph_span.span.before_placing(container)
        assert container.advance2(descender)

        # horizontal displacement
        left = self.indent

        if self._has_tab or text_align == TextAlign.JUSTIFY and last_line:
            text_align = 'left'
        extra_space = self.width - self.cursor
        if text_align == TextAlign.JUSTIFY:
            # TODO: padding added to spaces should be prop. to font size
            nr_spaces = sum(glyph_span.number_of_spaces for glyph_span in self)
            if nr_spaces > 0:
                add_to_spaces = extra_space / nr_spaces
                for glyph_span in self:
                    if glyph_span.number_of_spaces > 0:
                        glyph_span.space.width += add_to_spaces
        elif text_align == TextAlign.CENTER:
            left += extra_space / 2.0
        elif text_align == TextAlign.RIGHT:
            left += extra_space

        canvas = container.canvas
        cursor = container.cursor
        current_annotation = AnnotationState(container)
        for span, glyph_and_widths in group_spans(self):
            try:
                width = canvas.show_glyphs(left, cursor, span, glyph_and_widths,
                                           container)
            except InlineFlowableException:
                ascender = span.ascender(document)
                if ascender > 0:
                    top = cursor - ascender
                else:
                    inline_height = span.virtual_container.height
                    top = cursor - span.descender(document) - inline_height
                span.virtual_container.place_at(container, left, top)
                width = span.width
            current_annotation.update(span, left, width)
            left += width
        current_annotation.place_if_any()


def group_spans(line):
    span = None
    glyph_and_widths = []
    for glyph_span in line:
        if glyph_span.span is not span:
            if span:
                yield span, glyph_and_widths
            span = glyph_span.span
            glyph_and_widths = []
        try:
            glyph_and_widths += glyph_span
        except TypeError:   # InlineFlowable
            yield glyph_span, None
            span = None
    if span:
        yield span, glyph_and_widths


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

    def update_annotation(self, span, annotation_type, left, width):
        annotation = getattr(span, annotation_type + '_annotation')
        annotation_rect = getattr(self, annotation_type)
        if annotation_rect and annotation is not annotation_rect.annotation:
            self.place_if_any(annotation_type)
        if annotation:
            container = self.container
            if annotation_rect and annotation is annotation_rect.annotation:
                annotation_rect.update(width, span.height(container),
                                       span.ascender(container))
            else:
                annotation_rect = AnnotationRect(annotation, left, width,
                                                 span.height(container),
                                                 span.ascender(container))
        else:
            annotation_rect = None
        setattr(self, annotation_type, annotation_rect)

    def update(self, span, left, width):
        if isinstance(span, AnnotatedSpan):
            self.update_annotation(span, 'anchor', left, width)
            self.update_annotation(span, 'link', left, width)

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
