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
from copy import copy
from functools import cached_property, partial
from itertools import chain, groupby, count
from os import path

from . import DATA_PATH
from .annotation import AnnotatedSpan
from .attribute import (Attribute, AttributeType, OptionSet, ParseError,
                        OverrideDefault, Integer)
from .dimension import Dimension, PT
from .flowable import Flowable, FlowableStyle, FlowableState, FlowableWidth
from .font import MissingGlyphException
from .hyphenator import Hyphenator
from .inline import InlineFlowable, InlineFlowableSpan
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


class Glyph(object):
    __slots__ = ('metrics', 'width', 'char')

    def __init__(self, metrics, width, char):
        self.metrics = metrics
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


class TextMetrics(SpanMetrics):
    """The metrics of a span of text and the glyphs for its characters

    These are looked up only once for each computed style (see
    :func:`text_metrics`), since this requires resolving many of the span's
    style attributes.

    """

    __slots__ = ('font', 'color', 'y_offset',
                 'get_glyph_metrics', 'chars_to_glyphs', 'space')

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
        self.get_glyph_metrics, self.chars_to_glyphs = \
            create_lig_kern(span, font, height, container)
        self.space, = self.chars_to_glyphs(' ')


def text_metrics(span, container):
    """Return the :class:`TextMetrics` for `span`

    These are shared by all spans with the same computed style.

    """
    computed_style = container.document.get_computed_style(span)
    if computed_style.text_metrics is None:
        computed_style.text_metrics = TextMetrics(span, container)
    return computed_style.text_metrics


def create_lig_kern(span, font, height, flowable_target):
    scale = height / font.units_per_em
    variant = span.get_style('font_variant', flowable_target)
    kerning = span.get_style('kerning', flowable_target)
    ligatures = span.get_style('ligatures', flowable_target)
    char_spacing = float(span.get_style('character_spacing', flowable_target))
    get_glyph_metrics = partial(font.get_glyph_metrics, variant=variant)
    # TODO: handle ligatures at span borders
    def lig_kern(chars):
        glyph_metrics = (get_glyph_metrics(char) for char in chars)
        chars_and_glyph_metrics = zip(chars, glyph_metrics)
        if ligatures:
            chars_and_glyph_metrics = form_ligatures(chars_and_glyph_metrics,
                                                     font.get_ligature)
        if kerning:
            glyphs_kern = kern(chars_and_glyph_metrics, font.get_kerning)
        else:
            glyphs_kern = [(char, glyph, 0.0)
                           for char, glyph in chars_and_glyph_metrics]
        return [Glyph(glyph_metrics, scale * (glyph_metrics.width
                                              + kern_adjust)
                                     + char_spacing, char)
                for char, glyph_metrics, kern_adjust in glyphs_kern]

    return get_glyph_metrics, lig_kern


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
    get_glyph = metrics.get_glyph_metrics
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


class LinePart(object):
    def hyphenate(self, container):
        return iter([])


class SpecialCharacter(LinePart):
    def __init__(self, span, metrics):
        self.glyphs_span = GlyphsSpan(span, metrics)

    def __iter__(self):
        yield self.glyphs_span

    def __getitem__(self, index):
        assert index == 0
        return self.glyphs_span

    @cached_property
    def width(self):
        return self.glyphs_span.width


class Space(SpecialCharacter):
    char = ' '

    def __init__(self, span, metrics):
        super().__init__(span, metrics)
        self.glyphs_span.append_space()


class Tab(SpecialCharacter):
    char = '\t'


class NewLine(SpecialCharacter):
    char = '\n'


class ZeroWidthSpace(SpecialCharacter):
    char = '\N{ZERO WIDTH SPACE}'


class ForwardSlash(SpecialCharacter):
    char = '/'


WHITESPACE = {
    ' ': Space,
    '\t': Tab,
    '\n': NewLine,
    '\N{ZERO WIDTH SPACE}': ZeroWidthSpace,
    '/': ForwardSlash,
}




class DefaultTabStops(object):
    def __init__(self, tab_width):
        self.tab_width = tab_width

    def __iter__(self):
        return (TabStop(i * self.tab_width) for i in count(1))


class ParagraphState(FlowableState):
    """The position of the next word to typeset in a paragraph's words

    Args:
        index (int): index of the next word in the paragraph's words
        first_word (Word): the remainder of a hyphenated word, to typeset
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

    """
    language = container.document.language
    word = Word()
    for span, metrics in spans:
        if metrics is None:     # inline flowable
            word.append(span.flow_inline(container, 0))
            continue
        no_break_after = span.get_style('no_break_after', container)
        if no_break_after == LANGUAGE_DEFAULT:
            no_break_after = language.no_break_after
        text = span.text(container)
        if not text and getattr(span, 'anchor_annotation', None):
            word.append(GlyphsSpan(span, metrics))   # place the anchor
        for special, chars in groupby(text, WHITESPACE.get):
            if special is ForwardSlash:
                if word:
                    yield word
                word = Word()
            elif special:
                word_string = str(word).strip()
                last_word = (word_string.rsplit(maxsplit=1)[-1]
                             if word_string else '')
                if not (last_word.lower() in no_break_after
                        and special is Space):
                    if word:
                        yield word
                    for _ in chars:
                        yield special(span, metrics)
                    word = Word()
                    continue
            part = ''.join(chars).replace('\N{NO-BREAK SPACE}', ' ')
            if word and word[-1].span is span:
                prev_glyphs_span = word.pop()
                part = str(prev_glyphs_span) + part
            glyphs = metrics.chars_to_glyphs(part)
            word.append(GlyphsSpan(span, metrics, glyphs))
    if word:
        yield word


def break_lines(words, index, first_word, width, indent, tab_stops,
                significant_whitespace, container):
    """Break `words` into lines of `width` (greedy first fit)

    The word that doesn't fit on a line is hyphenated if possible. Otherwise,
    it moves to the next line, unless it is the line's first word.

    Args:
        words (list): the paragraph's words, spaces and special characters
        index (int): index of the first word to typeset
        first_word (Word): typeset before `words[index]` (the remainder of
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
            if isinstance(word, NewLine):
                if not wrapped:     # ignore newlines directly after a wrap
                    line.append(word.glyphs_span)
                    break
            elif line.append_word(word):
                wrapped = False
            else:
                wrapped = True
                for first, second, is_last in word.hyphenate(container):
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
        if not any(isinstance(glyphs_span, InlineFlowableSpan)
                   for word in words for glyphs_span in word):
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


class GlyphsSpan(list):
    def __init__(self, span, metrics, glyphs=()):
        space = metrics.space
        super().__init__(space if glyph.char == ' ' else glyph
                         for glyph in glyphs)
        self.span = span
        self.metrics = metrics
        self.space = space
        self.filled_tabs = {}

    def __str__(self):
        return ''.join(glyph.char for glyph in self)

    @property
    def width(self):
        return sum(glyph.width for glyph in self)

    @property
    def number_of_spaces(self):
        return self.count(self.space)

    @property
    def ends_with_space(self):
        return self[-1] == self.space

    def append_space(self):
        self.append(self.space)

    def widen_spaces(self, extra_width):
        """Return a copy of this glyphs span with wider spaces"""
        space = self.space
        result = copy(self)
        result.space = Glyph(space.metrics, space.width + extra_width,
                             space.char)
        result[:] = (result.space if glyph is space else glyph
                     for glyph in list.__iter__(self))
        return result

    def _fill_tabs(self):
        for index, glyph in enumerate(super().__iter__()):
            if index in self.filled_tabs:
                fill_string = self.filled_tabs[index]
                fill_glyphs = self.metrics.chars_to_glyphs(fill_string)
                fill_string_width = sum(glyph.width for glyph in fill_glyphs)
                number, rest = divmod(glyph.width, fill_string_width)
                yield Glyph(glyph.metrics, rest, glyph.char)
                for i in range(int(number)):
                    for fill_glyph in fill_glyphs:
                        yield fill_glyph
            else:
                yield glyph

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

    def __repr__(self):
        return f"{type(self).__name__}('{self}')"

    @cached_property
    def width(self):
        return sum(glyph_span.width for glyph_span in self)

    def hyphenate(self, container):
        # TODO: hyphenate mixed-styled words (if lang is the same)
        if len(self) > 1:
            return
        glyphs_span, = self
        span, metrics = glyphs_span.span, glyphs_span.metrics
        hyphenate = create_hyphenate(span, container)
        words = str(self).split()
        for i, word in enumerate(words):
            for first, second, is_last in hyphenate(word):
                f = chain(words[:i], [first])
                s = chain([second], words[i+1:])
                c2g = metrics.chars_to_glyphs
                first_gs = GlyphsSpan(span, metrics, c2g(' '.join(f)))
                second_gs = GlyphsSpan(span, metrics, c2g(' '.join(s)))
                yield Word([first_gs]), Word([second_gs]), is_last


class Line(list):
    """Helper class for building and typesetting a single line of text within
    a paragraph.

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
        self._has_tab = False
        self._current_tab = None
        self._current_tab_stop = None
        self.warnings = []      # (span, message) tuples

    def __str__(self):
        return ''.join(str(word) for word in self)

    def __repr__(self):
        return f"{type(self).__name__}('{self}')"

    def _handle_tab(self, glyphs_span):
        span = glyphs_span.span
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self.cursor < tab_position:
                tab_width = tab_position - self.cursor
                tab = Glyph(glyphs_span.space.metrics, tab_width, '\t')
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
            self.warnings.append((span, 'Tab did not fall into any of the '
                                        'tab stops.'))

    def append_word(self, word_or_inline, force=False):
        if isinstance(word_or_inline, Space):
            if not self and (not self.significant_whitespace
                             or self.wrapped_line):
                return True
        elif isinstance(word_or_inline, Tab):
            empty_glyphs_span = copy(word_or_inline.glyphs_span)
            empty_glyphs_span.filled_tabs = {}
            self._handle_tab(empty_glyphs_span)
            self.append(empty_glyphs_span)
            return True
        first_glyphs_span = word_or_inline[0]
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
                self.warnings.append((first_glyphs_span.span,
                                      'Tab space exceeded.'))
                current_tab.width = 0
                self._current_tab = None
            self.cursor -= item_width
        if self.cursor + width > self.width:
            if self or not force:
                return False
            elif self.width > 0:
                self.warnings.append((first_glyphs_span.span,
                                      'item too long to fit on line'))
        self.cursor += width
        for glyphs_span in word_or_inline:
            self.append(glyphs_span)
        return True

    @property
    def ascender(self):
        return max(glyph_span.metrics.ascender for glyph_span in self)

    @property
    def descender(self):
        return min(glyph_span.metrics.descender for glyph_span in self)

    @property
    def height(self):
        return max(glyph_span.metrics.height for glyph_span in self)

    @property
    def line_gap(self):
        return max(glyph_span.metrics.line_gap for glyph_span in self)

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
            last_span = self[-1]
            if last_span and last_span.ends_with_space:
                self.cursor -= last_span.space.width
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
        for glyph_span in self:
            glyph_span.span.before_placing(container, preallocate=True)
        assert container.advance2(descender)

        # horizontal displacement
        left = self.indent

        if self._current_tab or text_align == TextAlign.JUSTIFY and last_line:
            text_align = 'left'
        extra_space = self.width - self.cursor
        if text_align == TextAlign.JUSTIFY:
            # TODO: padding added to spaces should be prop. to font size
            nr_spaces = sum(glyph_span.number_of_spaces for glyph_span in self)
            if nr_spaces > 0:
                add_to_spaces = extra_space / nr_spaces
                for index, glyph_span in enumerate(self):
                    if glyph_span.number_of_spaces > 0:
                        self[index] = glyph_span.widen_spaces(add_to_spaces)
        elif text_align == TextAlign.CENTER:
            left += extra_space / 2.0
        elif text_align == TextAlign.RIGHT:
            left += extra_space

        document = container.document
        canvas = container.canvas
        cursor = container.cursor
        current_annotation = AnnotationState(container)
        for span, metrics, glyphs in group_spans(self):
            if glyphs is None:      # inline flowable
                if metrics.ascender > 0:
                    top = cursor - metrics.ascender
                else:
                    inline_height = span.virtual_container.height
                    top = cursor - metrics.descender - inline_height
                span.virtual_container.place_at(container, left, top)
                width = span.width
            else:
                width = canvas.show_glyphs(left, cursor, metrics, glyphs,
                                           document)
            current_annotation.update(span, metrics, left, width)
            left += width
        current_annotation.place_if_any()


def group_spans(line):
    """Group consecutive glyphs spans belonging to the same span

    Yields:
        (span, metrics, glyphs): `glyphs` is `None` for an inline flowable

    """
    span = None
    for glyph_span in line:
        if isinstance(glyph_span, InlineFlowableSpan):
            if span:
                yield span, metrics, glyphs
            yield glyph_span, glyph_span.metrics, None
            span = None
        elif glyph_span.span is not span:
            if span:
                yield span, metrics, glyphs
            span, metrics = glyph_span.span, glyph_span.metrics
            glyphs = list(glyph_span)
        else:
            glyphs += glyph_span
    if span:
        yield span, metrics, glyphs


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
