# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Classes for representing paragraphs and typesetting them:

* :class:`Paragraph`: A paragraph of mixed-styled text.
* :class:`ParagraphStyle`: Style class specifying paragraph formatting.
* :class:`TabStop`: Horizontal position for aligning text of successive lines.

The `line_spacing` option in a :class:`ParagraphStyle` can be any of:

* :class:`ProportionalSpacing`: Line spacing proportional to the line height.
* :class:`FixedSpacing`: Fixed line spacing, with optional minimum spacing.
* :class:`Leading`: Line spacing determined by the space in between two lines.
* :const:`DEFAULT`: The default line spacing as specified by the font.
* :const:`STANDARD`: Line spacing equal to 120% of the line height.
* :const:`SINGLE`: Line spacing equal to the line height (no leading).
* :const:`DOUBLE`: Line spacing of double the line height.

Horizontal justification of lines can be one of:

* :const:`LEFT`
* :const:`RIGHT`
* :const:`CENTER`
* :const:`BOTH`

"""

import os

from copy import copy
from functools import lru_cache, partial
from itertools import tee

from . import DATA_PATH
from .dimension import DimensionBase, PT
from .flowable import Flowable, FlowableStyle, FlowableState
from .font.style import SMALL_CAPITAL
from .hyphenator import Hyphenator
from .inline import InlineFlowableException
from .layout import EndOfContainer
from .text import TextStyle, MixedStyledText


__all__ = ['Paragraph', 'ParagraphStyle', 'TabStop',
           'ProportionalSpacing', 'FixedSpacing', 'Leading',
           'DEFAULT', 'STANDARD', 'SINGLE', 'DOUBLE',
           'LEFT', 'RIGHT', 'CENTER', 'BOTH']


# Text justification

from .flowable import LEFT, RIGHT, CENTER
BOTH = 'justify'


# Line spacing

class LineSpacing(object):
    """Base class for line spacing types. Line spacing is defined as the
    distance between the baselines of two consecutive lines."""

    def advance(self, line, last_descender, container):
        """Return the distance between the descender of the previous line and
        the baseline of the current line."""
        raise NotImplementedError


class DefaultSpacing(LineSpacing):
    """The default line spacing as specified by the font."""

    def advance(self, line, last_descender, container):
        max_line_gap = max(float(glyph_span.span.line_gap(container))
                           for glyph_span in line)
        ascender = max(float(glyph_span.span.ascender(container))
                       for glyph_span in line)
        return ascender + max_line_gap


DEFAULT = DefaultSpacing()
"""The default line spacing as specified by the font."""


class ProportionalSpacing(LineSpacing):
    """Line spacing proportional to the line height."""

    def __init__(self, factor):
        """`factor` specifies the amount by which the line height is multiplied
        to obtain the line spacing."""
        self.factor = factor

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
    """Fixed line spacing, with optional minimum spacing."""

    def __init__(self, pitch, minimum=SINGLE):
        """`pitch` specifies the distance between the baseline of two
        consecutive lines of text.
        Optionally, `minimum` specifies the minimum :class:`LineSpacing` to use,
        which can prevent lines with large fonts from overlapping. If no minimum
        is required, set to `None`."""
        self.pitch = float(pitch)
        self.minimum = minimum

    def advance(self, line, last_descender, container):
        advance = self.pitch + last_descender
        if self.minimum is not None:
            minimum = self.minimum.advance(line, last_descender, container)
            return max(advance, minimum)
        else:
            return advance


class Leading(LineSpacing):
    """Line spacing determined by the space in between two lines."""

    def __init__(self, leading):
        """`leading` specifies the space between the bottom of a line and the
        top of the following line."""
        self.leading = float(leading)

    def advance(self, line, last_descender):
        ascender = max(float(item.ascender) for item in line)
        return ascender + self.leading


class TabStop(object):
    """Horizontal position for aligning text of successive lines."""

    def __init__(self, position, align=LEFT, fill=None):
        """`position` can be an absolute position (:class:`Dimension`) or can
        be relative to the line width (:class:`float`, between 0 and 1).
        The alingment of text with respect to the tab stop is determined by
        `align`, which can be :const:`LEFT`, :const:`RIGHT` or :const:`CENTER`.
        Optionally, `fill` specifies a string pattern to fill the empty tab
        space with."""
        self._position = position
        self.align = align
        self.fill = fill

    def get_position(self, line_width):
        """Return the absolute position of this tab stop."""
        if isinstance(self._position, DimensionBase):
            return float(self._position)
        else:
            return line_width * self._position


# TODO: look at Word/OpenOffice for more options
class ParagraphStyle(FlowableStyle, TextStyle):
    """The :class:`Style` for :class:`Paragraph` objects. It has the following
    attributes:

    * `indent_first`: Indentation of the first line of text (class:`Dimension`).
    * `line_spacing`: Spacing between the baselines of two successive lines of
                      text (:class:`LineSpacing`).
    * `justify`: Alignment of the text to the margins (:const:`LEFT`,
                 :const:`RIGHT`, :const:`CENTER` or :const:`BOTH`).
    * `tab_stops`: The tab stops for this paragraph (list of :class:`TabStop`).
    """

    attributes = {'indent_first': 0*PT,
                  'line_spacing': DEFAULT,
                  'justify': BOTH,
                  'tab_stops': []}


# TODO: shouldn't take a container (but needed by flow_inline)
# (return InlineFlowableSpan that raises InlineFlowableException later)
def spans_to_words(spans, container):
    word = Word()
    for span in spans:
        try:
            word_to_glyphs = create_to_glyphs(span, container)
            for chars in span.split(container):
                glyphs_span = GlyphsSpan(span, word_to_glyphs)
                glyphs_span += word_to_glyphs(chars)
                if chars in (' ', '\t', '\n', '\N{ZERO WIDTH SPACE}'):
                    if word:
                        yield word
                    if chars != '\N{ZERO WIDTH SPACE}':
                        yield Word([(glyphs_span, chars)])
                    word = Word()
                else:
                    word.append((glyphs_span, chars))
        except InlineFlowableException:
            # TODO: take descender into account
            glyphs_span = span.flow_inline(container, 0)
            word.append((glyphs_span, '<inline image>'))
    if word:
        yield word


class ParagraphState(FlowableState):
    def __init__(self, words, nested_flowable_state=None, _first_word=None,
                 _initial=True):
        super().__init__(_initial)
        self._words = words
        self.nested_flowable_state = nested_flowable_state
        self._first_word = _first_word

    def __copy__(self):
        copy_words, self._words = tee(self._words)
        copy_nested_flowable_state = copy(self.nested_flowable_state)
        return self.__class__(copy_words, copy_nested_flowable_state,
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
    """A paragraph of mixed-styled text that can be flowed into a
    :class:`Container`."""

    style_class = ParagraphStyle

    def render(self, container, descender, state=None):
        """Typeset the paragraph onto `container`, starting below the current
        cursor position of the container. `descender` is the descender height of
        the preceeding line or `None`.
        When the end of the container is reached, the rendering state is
        preserved to continue setting the rest of the paragraph when this method
        is called with a new container."""
        indent_first = (0 if state
                        else float(self.get_style('indent_first', container)))
        line_width = float(container.width)
        line_spacing = self.get_style('line_spacing', container)
        justification = self.get_style('justify', container)
        tab_stops = self.get_style('tab_stops', container)

        # `saved_state` is updated after successfully rendering each line, so
        # that when `container` overflows on rendering a line, the words in that
        # line are yielded again on the next typeset() call.
        if not state:
            spans = self.text(container).spans(container.document)
            state = ParagraphState(spans_to_words(spans, container))
        saved_state = copy(state)
        prev_state = copy(state)
        max_line_width = 0

        def typeset_line(line, last_line=False, force=False):
            """Typeset `line` and, if no exception is raised, update the
            paragraph's internal rendering state."""
            nonlocal state, saved_state, max_line_width, descender
            try:
                max_line_width = max(max_line_width, line.cursor)
                descender = line.typeset(container, justification, line_spacing,
                                         descender, last_line, force)
                state.initial = False
                saved_state = copy(state)
                return Line(tab_stops, line_width, container)
            except EndOfContainer:
                raise EndOfContainer(saved_state)

        line = Line(tab_stops, line_width, container, indent_first)
        while True:
            try:
                word = state.next_word()
            except StopIteration:
                break
            if word.is_newline:
                (glyphs_span, chars), = word
                gs = GlyphsSpan(glyphs_span.span, glyphs_span.word_to_glyphs)
                line.append(gs)
                line = typeset_line(line, last_line=True, force=True)
            elif not line.append_word(word, container, descender):
                for first, second in word.hyphenate(container):
                    if line.append_word(first, container, descender):
                        state.prepend_word(second)  # prepend second part
                        break
                else:
                    state = prev_state
                line = typeset_line(line)
                continue
            if not word.is_space:
                prev_state = copy(state)
        if line:
            typeset_line(line, last_line=True)

        return max_line_width, descender


class Paragraph(ParagraphBase, MixedStyledText):
    def __init__(self, text_or_items, id=None, style=None, parent=None):
        """See :class:`MixedStyledText`. As a paragraph typically doesn't have
        a parent, `style` should be specified."""
        MixedStyledText.__init__(self, text_or_items, style=style,
                                 parent=parent)
        self.id = id

    def text(self, container):
        return self


class HyphenatorStore(dict):
    def __missing__(self, key):
        hyphen_lang, hyphen_chars = key
        dic_path = dic_file = 'hyph_{}.dic'.format(hyphen_lang)
        if not os.path.exists(dic_path):
            dic_path = os.path.join(os.path.join(DATA_PATH, 'hyphen'), dic_file)
            if not os.path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))
        self[key] = hyphenator = Hyphenator(dic_path, hyphen_chars, hyphen_chars)
        return hyphenator


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


class GlyphAndWidth(object):
    __slots__ = ('glyph', 'width')

    def __init__(self, glyph, width):
        self.glyph = glyph
        self.width = width


@lru_cache()
def create_to_glyphs(span, flowable_target):
    font = span.font(flowable_target)
    scale = span.height(flowable_target) / font.units_per_em
    variant = (SMALL_CAPITAL if span.get_style('small_caps', flowable_target)
               else None)
    kerning = span.get_style('kerning', flowable_target)
    ligatures = span.get_style('ligatures', flowable_target)
    get_glyph = partial(font.get_glyph, variant=variant)
    # TODO: handle ligatures at span borders
    def word_to_glyphs(word):
        glyphs = [get_glyph(char) for char in word]
        if ligatures:
            glyphs = form_ligatures(glyphs, font.get_ligature)
        if kerning:
            glyphs_kern = kern(glyphs, font.get_kerning)
        else:
            glyphs_kern = [(glyph, 0.0) for glyph in glyphs]
        return [GlyphAndWidth(glyph, scale * (glyph.width + kern_adjust))
                for glyph, kern_adjust in glyphs_kern]

    return word_to_glyphs


def form_ligatures(glyphs, get_ligature):
    glyphs = iter(glyphs)
    result = []
    prev_glyph = next(glyphs)
    for glyph in glyphs:
        ligature_glyph = get_ligature(prev_glyph, glyph)
        if ligature_glyph:
            prev_glyph = ligature_glyph
        else:
            result.append(prev_glyph)
            prev_glyph = glyph
    result.append(prev_glyph)
    return result


def kern(glyphs, get_kerning):
    glyphs = iter(glyphs)
    result = []
    prev_glyph = next(glyphs)
    for glyph in glyphs:
        result.append((prev_glyph, get_kerning(prev_glyph, glyph)))
        prev_glyph = glyph
    result.append((prev_glyph, 0.0))
    return result


class GlyphsSpan(list):
    def __init__(self, span, word_to_glyphs):
        super().__init__()
        self.span = span
        self.filled_tabs = {}
        self.word_to_glyphs = word_to_glyphs
        self.space = word_to_glyphs(' ')[0]

    @property
    def width(self):
        return sum(item.width for item in self)

    @property
    def number_of_spaces(self):
        return self.count(self.space)

    @property
    def ends_with_space(self):
        return self[-1] is self.space

    def append_space(self):
        self.append(self.space)

    def _fill_tabs(self):
        for index, glyph_and_width in enumerate(super().__iter__()):
            if index in self.filled_tabs:
                fill_string = self.filled_tabs[index]
                fill_glyphs = self.word_to_glyphs(fill_string)
                fill_string_width = sum(glyph.width for glyph in fill_glyphs)
                number, rest = divmod(glyph_and_width.width, fill_string_width)
                yield GlyphAndWidth(glyph_and_width.glyph, rest)
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


class Word(list):
    def __init__(self, glyphspan_chars_pairs=None):
        super().__init__(glyphspan_chars_pairs or [])

    def __str__(self):
        return ''.join(chars for glyphs_span, chars in self)

    @property
    def is_space(self):
        return self[0][1] in (' ', '\t')

    @property
    def is_newline(self):
        return self[0][1] == '\n'

    @property
    def width(self):
        return sum(glyph_span.width for glyph_span, chars in self)

    def hyphenate(self, container):
        # TODO: hyphenate mixed-styled words (if lang is the same)
        if len(self) > 1:
            return
        first_glyphs_span, first_chars = self[0]
        span = first_glyphs_span.span
        w2g = first_glyphs_span.word_to_glyphs
        hyphenate = create_hyphenate(first_glyphs_span.span, container)
        for first, second in hyphenate(str(self)):
            first_gs = GlyphsSpan(span, w2g)
            first_gs += w2g(first)
            second_gs = GlyphsSpan(span, w2g)
            second_gs += w2g(second)
            yield Word([(first_gs, first)]), Word([(second_gs, second)])


class Line(list):
    """Helper class for building and typesetting a single line of text within
    a :class:`Paragraph`."""

    def __init__(self, tab_stops, width, container, indent=0):
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
        self._has_tab = False
        self._current_tab = None
        self._current_tab_stop = None

    def _handle_tab(self, glyphs_span, span):
        if not self.tab_stops:
            span.warn('No tab stops defined for this paragraph style.',
                      self.container)
            self.cursor += glyphs_span.space.width
            glyphs_span.append_space()
            return
        self._has_tab = True
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self.cursor < tab_position:
                tab_width = tab_position - self.cursor
                tab = GlyphAndWidth(glyphs_span.space.glyph, tab_width)
                if tab_stop.fill:
                    glyphs_span.filled_tabs[len(glyphs_span)] = tab_stop.fill
                glyphs_span.append(tab)
                self.cursor = tab_position
                self._current_tab_stop = tab_stop
                if tab_stop.align in (RIGHT, CENTER):
                    self._current_tab = tab
                    self._current_tab_stop = tab_stop
                else:
                    self._current_tab = None
                    self._current_tab_stop = None
                break
        else:
            span.warn('Tab did not fall into any of the tab stops.',
                      self.container)

    def append_word(self, word_or_inline, container, descender):
        try:
            first_glyphs_span, first_chars = word_or_inline[0]
        except TypeError:
            return self.add_flowable(word_or_inline, container, descender)

        if first_chars == ' ':
            if not self:
                return True
            first_glyphs_span.space = first_glyphs_span[0]
        elif first_chars == '\t':
            empty_glyphs_span = GlyphsSpan(first_glyphs_span.span,
                                           first_glyphs_span.word_to_glyphs)
            self._handle_tab(empty_glyphs_span, empty_glyphs_span.span)
            self.append(empty_glyphs_span)
            return True
        width = word_or_inline.width
        if self._current_tab:
            current_tab = self._current_tab
            tab_width = current_tab.width
            factor = 2 if self._current_tab_stop.align == CENTER else 1
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
        for glyphs_span, chars in word_or_inline:
            self.append(glyphs_span)
        return True

    def typeset(self, container, justification, line_spacing, last_descender,
                last_line=False, force=False):
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
            return last_descender

        descender = min(glyph_span.span.descender(container)
                        for glyph_span in self)
        if last_descender is None:
            advance = max(glyph_span.span.ascender(container)
                          for glyph_span in self)
        else:
            advance = line_spacing.advance(self, last_descender, container)
        container.advance(advance)

        container.advance(- descender)
        for glyph_span in self:
            glyph_span.span.before_placing(container)
        container.advance(descender)

        # horizontal displacement
        left = self.indent

        if self._has_tab or justification == BOTH and last_line:
            justification = LEFT
        extra_space = self.width - self.cursor
        if justification == BOTH:
            # TODO: padding added to spaces should be prop. to font size
            nr_spaces = sum(glyph_span.number_of_spaces for glyph_span in self)
            if nr_spaces > 0:
                add_to_spaces = extra_space / nr_spaces
                for glyph_span in self:
                    if glyph_span.number_of_spaces > 0:
                        glyph_span.space.width += add_to_spaces
        elif justification == CENTER:
            left += extra_space / 2.0
        elif justification == RIGHT:
            left += extra_space

        canvas = container.canvas
        cursor = container.cursor
        current_annotation = AnnotationState(container)
        for span, glyph_and_widths in group_spans(self):
            try:
                width = canvas.show_glyphs(left, cursor, span, glyph_and_widths,
                                           container)
            except InlineFlowableException:
                top = cursor - span.ascender(document)
                span.virtual_container.place_at(container, left, top)
                width = span.width
            current_annotation.update(span, left, width)
            left += width
        current_annotation.place_if_any()
        container.advance(- descender)
        return descender


def group_spans(line):
    span = None
    glyph_and_widths = []
    for glyph_span in line:
        if glyph_span.span != span:
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


class AnnotationState(object):
    __slots__ = ('annotation', 'left', 'width', 'ascender', 'height',
                 'container')

    def __init__(self, container):
        self.annotation = None
        self.container = container

    def update(self, span, left, width):
        if not hasattr(span, 'annotation'):
            return
        annotation = span.annotation
        if annotation is not self.annotation:
            self.place_if_any()
        if annotation:
            container = self.container
            if annotation is self.annotation:
                self.width += width
                self.ascender = max(self.ascender, span.ascender(container))
                self.height = max(self.height, span.height(container))
            else:
                self.left = left
                self.width = width
                self.ascender = span.ascender(container)
                self.height = span.height(container)
        self.annotation = annotation

    def place_if_any(self):
        if self.annotation:
            top = self.container.cursor - self.ascender
            self.container.canvas.annotate(self.annotation, self.left, top,
                                           self.width, self.height)
