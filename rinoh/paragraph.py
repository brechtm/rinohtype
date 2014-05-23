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

The line spacing option in a :class:`ParagraphStyle` can be any of:

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
from .layout import EndOfContainer
from .text import TextStyle, MixedStyledText
from .util import consumer


__all__ = ['Paragraph', 'ParagraphStyle', 'TabStop',
           'ProportionalSpacing', 'FixedSpacing', 'Leading',
           'DEFAULT', 'STANDARD', 'SINGLE', 'DOUBLE',
           'LEFT', 'RIGHT', 'CENTER', 'BOTH']


# Text justification

LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'
BOTH = 'justify'


# Line spacing

class LineSpacing(object):
    """Base class for line spacing types. Line spacing is defined as the
    distance between the baselines of two consecutive lines."""

    def advance(self, line, last_descender, document):
        """Return the distance between the descender of the previous line and
        the baseline of the current line."""
        raise NotImplementedError


class DefaultSpacing(LineSpacing):
    """The default line spacing as specified by the font."""

    def advance(self, line, last_descender, document):
        max_line_gap = max(float(glyph_span.span.line_gap(document))
                           for glyph_span in line)
        ascender = max(float(glyph_span.span.ascender(document))
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

    def advance(self, line, last_descender, document):
        max_font_size = max(float(glyph_span.span.height(document))
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

    def advance(self, line, last_descender, document):
        advance = self.pitch + last_descender
        if self.minimum is not None:
            minimum = self.minimum.advance(line, last_descender, document)
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
class ParagraphStyle(TextStyle, FlowableStyle):
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

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class ParagraphState(FlowableState):
    def __init__(self, spans, first_line=True, nested_flowable_state=None,
                 _current_span=None, _items=None, _current_item=None):
        self.spans = spans
        self.current_span = _current_span or None
        self.items = _items or iter([])
        self.current_item = _current_item or None
        self.first_line = first_line
        self.nested_flowable_state = nested_flowable_state

    def __copy__(self):
        copy_spans, self.spans = tee(self.spans)
        copy_items, self.items = tee(self.items)
        copy_nested_flowable_state = copy(self.nested_flowable_state)
        return self.__class__(copy_spans, self.first_line,
                              copy_nested_flowable_state,
                              _current_span=self.current_span,
                              _items=copy_items,
                              _current_item=self.current_item)

    def next_item(self, container):
        if self.current_item:
            self.current_item, current_item = None, self.current_item
            return self.current_span, current_item
        try:
            return self.current_span, next(self.items)
        except StopIteration:
            self.current_span = next(self.spans)
            self.items = self.current_span.split(container)
            return self.next_item(container)

    def prepend_item(self, item):
        self.current_item = item


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
        document = container.document
        indent_first = 0 if state else float(self.get_style('indent_first',
                                                            document))
        line_width = float(container.width)
        line_spacing = self.get_style('line_spacing', document)
        justification = self.get_style('justify', document)
        tab_stops = self.get_style('tab_stops', document)

        # `saved_state` is updated after successfully rendering each line, so
        # that when `container` overflows on rendering a line, the words in that
        # line are yielded again on the next typeset() call.
        state = state or ParagraphState(self.text(document).spans())
        saved_state = copy(state)
        max_line_width = 0

        def typeset_line(line, last_line=False, force=False):
            """Typeset `line` and, if no exception is raised, update the
            paragraph's internal rendering state."""
            nonlocal span, state, saved_state, max_line_width, descender
            try:
                max_line_width = max(max_line_width, line._cursor)
                descender = line.typeset(container, justification, line_spacing,
                                         descender, last_line, force)
                saved_state = copy(state)
                return Line(tab_stops, line_width, container)
            except EndOfContainer:
                raise EndOfContainer(saved_state)

        line = Line(tab_stops, line_width, container, indent_first)
        last_span = None
        while True:
            try:
                span, word = state.next_item(container)  # raises StopIteration
                if span is not last_span:
                    line_span_send = line.new_span(span, document).send
                    hyphenate = create_hyphenate(span, document)
                    last_span = span

                if word == '\n':
                    line = typeset_line(line, last_line=True, force=True)
                    line_span_send = line.new_span(span, document).send
                elif not line_span_send(word):
                    for first, second in hyphenate(word):
                        if line_span_send(first):
                            state.prepend_item(second)
                            break
                    else:
                        state.prepend_item(word)
                    line = typeset_line(line)
                    line_span_send = line.new_span(span, document).send
            except StopIteration:
                if line:
                    typeset_line(line, last_line=True)
                break

        return max_line_width, descender


class Paragraph(ParagraphBase, MixedStyledText):
    def __init__(self, text_or_items, style=None, parent=None):
        """See :class:`MixedStyledText`. As a paragraph typically doesn't have
        a parent, `style` should be specified."""
        MixedStyledText.__init__(self, text_or_items, style=style, parent=parent)

    def text(self, document):
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


def create_hyphenate(span, document):
    if not span.get_style('hyphenate', document):
        def dont_hyphenate(word):
            return
            yield
        return dont_hyphenate

    hyphenator = HYPHENATORS[span.get_style('hyphen_lang', document),
                             span.get_style('hyphen_chars', document)]
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
def create_to_glyphs(font, scale, variant, kerning, ligatures):
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
        self.number_of_spaces = 0
        self.space = word_to_glyphs(' ')[0]

    def append_space(self):
        self.number_of_spaces += 1
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
        self._cursor = indent
        self._has_tab = False
        self._has_filled_tab = False
        self._current_tab = None
        self._current_tab_stop = None

    def _handle_tab(self, glyphs_span, span):
        if not self.tab_stops:
            span.warn('No tab stops defined for this  paragraph style.',
                      self.container)
            self._cursor += glyphs_span.space.width
            glyphs_span.append_space()
            return
        self._has_tab = True
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self._cursor < tab_position:
                tab_width = tab_position - self._cursor
                tab = GlyphAndWidth(glyphs_span.space.glyph, tab_width)
                if tab_stop.fill:
                    self._has_filled_tab = True
                    glyphs_span.filled_tabs[len(glyphs_span)] = tab_stop.fill
                glyphs_span.append(tab)
                self._cursor += tab_width
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

    @consumer
    def new_span(self, span, document):
        font = span.font(document)
        scale = span.height(document) / font.units_per_em
        variant = (SMALL_CAPITAL if span.get_style('small_caps', document) else None)
        word_to_glyphs = create_to_glyphs(font, scale, variant,
                                          span.get_style('kerning', document),
                                          span.get_style('ligatures', document))
        glyphs_span = GlyphsSpan(span, word_to_glyphs)
        super().append(glyphs_span)

        success = True
        while True:
            word = (yield success)
            success = True
            if word == ' ':
                self._cursor += glyphs_span.space.width
                glyphs_span.append_space()
            elif word == '\t':
                self._handle_tab(glyphs_span, span)
            else:
                glyphs_and_widths = word_to_glyphs(word)
                width = sum(glyph.width for glyph in glyphs_and_widths)
                if self._current_tab:
                    current_tab = self._current_tab
                    tab_width = current_tab.width
                    factor = 2 if self._current_tab_stop.align == CENTER else 1
                    item_width = width / factor
                    if item_width < tab_width:
                        current_tab.width -= item_width
                    else:
                        span.warn('Tab space exceeded.', self.container)
                        current_tab.width = 0
                        self._current_tab = None
                    self._cursor -= tab_width
                if self._cursor + width > self.width:
                    if not self[0]:
                        span.warn('item too long to fit on line',
                                  self.container)
                    else:
                        success = False
                        continue
                self._cursor += width
                glyphs_span += glyphs_and_widths

    def add_flowable(self, flowable, document):
        pass

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
        while self:
            last_span = self[-1]
            while last_span and last_span[-1] is last_span.space:
                last_span.pop()
                last_span.number_of_spaces -= 1
                self._cursor -= last_span.space.width
            if last_span or (force and len(self) == 1):
                break
            self.pop()
        else:   # abort if the line is empty
            return last_descender

        descender = min(glyph_span.span.descender(document)
                        for glyph_span in self)
        if last_descender is None:
            advance = max(glyph_span.span.ascender(document)
                          for glyph_span in self)
        else:
            advance = line_spacing.advance(self, last_descender, document)
        container.advance(advance)
        if - descender > container.remaining_height:
            raise EndOfContainer

        # horizontal displacement
        left = self.indent

        if self._has_tab or justification == BOTH and last_line:
            justification = LEFT
        extra_space = self.width - self._cursor
        if justification == BOTH:
            # TODO: padding added to spaces should be prop. to font size
            nr_spaces = sum(glyph_span.number_of_spaces for glyph_span in self)
            if nr_spaces > 0:
                add_to_spaces = extra_space / nr_spaces
                for glyph_span in self:
                    glyph_span.space.width += add_to_spaces
        elif justification == CENTER:
            left += extra_space / 2.0
        elif justification == RIGHT:
            left += extra_space

        for glyph_span in self:
            left += container.canvas.show_glyphs(left, container.cursor,
                                                 glyph_span, document)
        container.advance(- descender)
        return descender
