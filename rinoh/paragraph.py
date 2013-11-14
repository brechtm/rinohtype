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

from collections import defaultdict
from copy import copy
from functools import partial
from itertools import chain, tee

from . import DATA_PATH
from .dimension import Dimension, PT
from .flowable import FlowableException, Flowable, FlowableStyle, FlowableState
from .font.style import SMALL_CAPITAL
from .hyphenator import Hyphenator
from .layout import EndOfContainer
from .reference import FieldException
from .text import NewlineException, TabException, TabSpaceExceeded
from .text import TextStyle, MixedStyledText


__all__ = ['Paragraph', 'ParagraphStyle', 'TabStop',
           'ProportionalSpacing', 'FixedSpacing', 'Leading',
           'DEFAULT', 'STANDARD', 'SINGLE', 'DOUBLE',
           'LEFT', 'RIGHT', 'CENTER', 'BOTH']


# Text justification

LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'
BOTH = 'justify'


try:
    profile
except NameError:
    def profile(function):
        return function


# Line spacing

class LineSpacing(object):
    """Base class for line spacing types. Line spacing is defined as the
    distance between the baselines of two consecutive lines."""

    def advance(self, line, last_descender):
        """Return the distance between the descender of the previous line and
        the baseline of the current line."""
        raise NotImplementedError


class DefaultSpacing(LineSpacing):
    """The default line spacing as specified by the font."""

    def advance(self, line, last_descender):
        max_line_gap = max(float(glyph_span.span.line_gap)
                           for glyph_span in line)
        ascender = max(float(glyph_span.span.ascender)
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

    def advance(self, line, last_descender):
        max_font_size = max(float(glyph_span.span.height)
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

    def advance(self, line, last_descender):
        advance = self.pitch + last_descender
        if self.minimum is not None:
            minimum = self.minimum.advance(line, last_descender)
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
        The alinment of text with respect to the tab stop is determined by
        `align`, which can be :const:`LEFT`, :const:`RIGHT` or :const:`CENTER`.
        Optionally, `fill` specifies a string pattern to fill the empty tab
        space with."""
        self._position = position
        self.align = align
        self.fill = fill

    def get_position(self, line_width):
        """Return the absolute position of this tab stop."""
        if isinstance(self._position, Dimension):
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
                 _copy=False):
        self.items = spans if _copy else self._form_span_item_pairs(spans)
        self.first_line = first_line
        self.nested_flowable_state = nested_flowable_state

    def __copy__(self):
        copy_items, self.items = tee(self.items)
        copy_nested_flowable_state = copy(self.nested_flowable_state)
        return self.__class__(copy_items, self.first_line,
                              copy_nested_flowable_state, _copy=True)

    def next_item(self):
        return next(self.items)

    def prepend_item(self, span, item):
        self.items = chain(((span, item), ), self.items)

    def prepend_spans(self, spans):
        self.items = chain(self._form_span_item_pairs(spans), self.items)

    @staticmethod
    def _form_span_item_pairs(spans):
        return ((span, item) for span in spans for item in span.split())


class Paragraph(MixedStyledText, Flowable):
    """A paragraph of mixed-styled text that can be flowed into a
    :class:`Container`."""

    style_class = ParagraphStyle

    split = Flowable.split

    def __init__(self, text_or_items, style=None, parent=None):
        """See :class:`MixedStyledText`. As a paragraph typically doesn't have
        a parent, `style` should be specified."""
        super().__init__(text_or_items, style=style, parent=parent)

    @profile
    def render(self, container, descender, state=None):
        """Typeset the paragraph onto `container`, starting below the current
        cursor position of the container. `descender` is the descender height of
        the preceeding line or `None`.
        When the end of the container is reached, the rendering state is
        preserved to continue setting the rest of the paragraph when this method
        is called with a new container."""
        indent_first = 0 if state else float(self.get_style('indent_first'))
        line_width = float(container.width)
        line_spacing = self.get_style('line_spacing')
        justification = self.get_style('justify')
        tab_stops = self.get_style('tab_stops')

        # `saved_state` is updated after successfully rendering each line, so
        # that when `container` overflows on rendering a line, the words in that
        # line are yielded again on the next typeset() call.
        state = state or ParagraphState(MixedStyledText.spans(self))
        saved_state = copy(state)

        def typeset_line(line, last_line=False):
            """Typeset `line` and, if no exception is raised, update the
            paragraph's internal rendering state."""
            nonlocal state, saved_state, descender
            try:
                if line:
                    descender = line.typeset(container, justification,
                                             line_spacing, descender, last_line)
                    saved_state = copy(state)
            except EndOfContainer:
                raise EndOfContainer(saved_state)

        line = Line(tab_stops, line_width, container, indent_first)
        span = None
        while True:
            try:
                new_span, word = state.next_item()      # raises StopIteration
                if new_span is not span:
                    span = new_span
                    to_glyphs, hyphenate = create_to_glyphs_and_hyphenate(span)
                    space_glyph_and_width = to_glyphs(' ')[0]
                    line.new_span(span, space_glyph_and_width)

                glyphs_and_widths = to_glyphs(word)
                if word == ' ':
                    line.append_space()
                elif not line.append(glyphs_and_widths):
                    for first, second in hyphenate(word):
                        glyphs_and_widths = to_glyphs(first)
                        if line.append(glyphs_and_widths):
                            state.prepend_item(span, second)
                            break
                    else:
                        state.prepend_item(span, word)
                    typeset_line(line)
                    line = Line(tab_stops, line_width, container)
                    line.new_span(span, space_glyph_and_width)
            except FieldException as e:
                state.prepend_spans(e.field_spans(container))
            except FlowableException as fe:
                typeset_line(line, last_line=True)
                try:
                    _, descender = fe.flowable.flow(container, descender,
                                                    state.nested_flowable_state)
                    state.nested_flowable_state = None
                except EndOfContainer as eoc:
                    state.prepend_item(fe.flowable, None)
                    state.nested_flowable_state = eoc.flowable_state
                    raise EndOfContainer(state)
                line = Line(tab_stops, line_width, container)
            except StopIteration:
                if line:
                    typeset_line(line, last_line=True)
                break

        return descender


def create_to_glyphs_and_hyphenate(span):
    font = span.font
    scale = span.height / font.units_per_em
    variant = (SMALL_CAPITAL if span.get_style('small_caps') else None)
    get_glyph = partial(font.metrics.get_glyph, variant=variant)
    kerning = span.get_style('kerning')
    ligatures = span.get_style('ligatures')
    # TODO: handle ligatures at span borders

    def word_to_glyphs(word):
        glyphs_widths = ((glyph, scale * glyph.width)
                         for glyph in (get_glyph(char) for char in word))
        if kerning:
            glyphs_widths = kern(glyphs_widths, font.metrics.get_kerning, scale)
        if ligatures:
            glyphs_widths = form_ligatures(glyphs_widths,
                                           font.metrics.get_ligature, scale)
        return list(glyphs_widths)

    if span.get_style('hyphenate'):
        hyphenate = create_hyphenate(span.get_style('hyphen_lang'),
                                     span.get_style('hyphen_chars'))
    else:
        hyphenate = dont_hyphenate

    return word_to_glyphs, hyphenate


def form_ligatures(glyphs_and_widths, get_ligature, scale):
    prev_glyph, prev_width = next(glyphs_and_widths)
    for glyph, width in glyphs_and_widths:
        ligature_glyph = get_ligature(prev_glyph, glyph)
        if ligature_glyph:
            prev_glyph = ligature_glyph
            prev_width = ligature_glyph.width * scale
        else:
            yield prev_glyph, prev_width
            prev_glyph, prev_width = glyph, width
    yield prev_glyph, prev_width


def kern(glyphs_and_widths, get_kerning, scale):
    prev_glyph, prev_width = next(glyphs_and_widths)
    for glyph, width in glyphs_and_widths:
        prev_width += get_kerning(prev_glyph, glyph) * scale
        yield prev_glyph, prev_width
        prev_glyph, prev_width = glyph, width
    yield prev_glyph, prev_width


class HyphenatorStore(defaultdict):
    def __missing__(self, key):
        hyphen_lang, hyphen_chars = key
        dic_path = dic_file = 'hyph_{}.dic'.format(hyphen_lang)
        if not os.path.exists(dic_path):
            dic_path = os.path.join(os.path.join(DATA_PATH, 'hyphen'), dic_file)
            if not os.path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))
        return Hyphenator(dic_path, hyphen_chars, hyphen_chars)


HYPHENATORS = HyphenatorStore()


def create_hyphenate(hyphen_lang, hyphen_chars):
    hyphenator = HYPHENATORS[hyphen_lang, hyphen_chars]
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


def dont_hyphenate(word):
    return
    yield


class GlyphsSpan(list):
    def __init__(self, span, space_glyph_and_width):
        super().__init__()
        self.span = span
        self.space_indices = set()
        self.space_glyph_and_width = space_glyph_and_width

    def append_space(self):
        self.space_indices.add(len(self))


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
        self._current_tab = None

    def new_span(self, parent, space_glyph_and_width):
        super().append(GlyphsSpan(parent, space_glyph_and_width))

    def append_space(self):
        self._cursor += self[-1].space_glyph_and_width[1]
        self[-1].append_space()

    def append_space(self, glyph_and_width):
        self._cursor += glyph_and_width[1]
        self[-1].append_space(glyph_and_width)

    # Line is a simple state machine. Different methods are assigned to
    # Line.append, depending on the current state.

    @profile
    def _normal_append(self, glyphs_and_widths):
        """Appends `item` to this line. If the item doesn't fit on the line,
        returns the spillover. Otherwise returns `None`."""
        width = sum(width for glyph, width in glyphs_and_widths)
        if self._cursor + width > self.width:
            if not self:
                self[-1].span.warn('item too long to fit on line',
                                   self.container)
            else:
                return False
        self._cursor += width
        self[-1].append(glyphs_and_widths)
        return True

    append = _normal_append

    def _tab_append(self, item):
        """Append method used when we are in the context of a right-, or center-
        aligned tab stop. This shrinks the width of the preceeding tab character
        in order to obtain the alignment."""
        tab_width = self._current_tab.tab_width
        try:
            factor = 2 if self._current_tab.tab_stop.align == CENTER else 1
            width = item.width / factor
            self._current_tab.shrink(width)
        except TabException:
            width, item = self._handle_tab(item)
        except TabSpaceExceeded:
            item.warn('Tab space exceeded.', self.container)
            self._cursor -= tab_width
            self.append = self._normal_append
            return self.append(item)
        self._cursor += width
        super().append(item)

    def _handle_tab(self, tab):
        """Called when a :class:`Tab` is appended to the line. Searches for the
        :class:`TabStop` `tab` jumps to. Returns a tuple containing:

        * the tab width (determined from the line cursor position and the tab
          stop), and
        * the tab itself, or a :class:`Space` (if no tab stop was found)."""
        if not self.tab_stops:
            tab.warn('No tab stops defined for this paragraph style.',
                     self.container)
            return 0, Space(style=tab.style, parent=tab.parent)
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self._cursor < tab_position:
                tab.tab_stop = tab_stop
                tab.tab_width = tab_position - self._cursor
                if tab_stop.align in (RIGHT, CENTER):
                    self._current_tab = tab
                    self.append = self._tab_append
                else:
                    self._current_tab = None
                    self.append = self._normal_append
                return tab.tab_width, tab
        else:
            tab.warn('Tab did not fall into any of the tab stops.')
            return 0, Space(style=tab.style, parent=tab.parent)

    @profile
    def typeset(self, container, justification, line_spacing, last_descender,
                last_line=False):
        """Typeset the line in `container` below its current cursor position.
        Advances the container's cursor to below the descender of this line.

        `justification` and `line_spacing` are passed on from the paragraph
        style. `last_descender` is the previous line's descender, used in the
        vertical positioning of this line. Finally, `last_line` specifies
        whether this is the last line of the paragraph.

        Returns the line's descender size."""
        # remove empty spans at the end of the line
        while len(self[-1]) == 0:
            self.pop()
        # drop space at the end of the line
        self[-1].space_indices.discard(len(self[-1]))

        descender = min(float(glyph_span.span.descender)
                        for glyph_span in self)
        if last_descender is None:
            advance = max(float(glyph_span.span.ascender)
                          for glyph_span in self)
        else:
            advance = line_spacing.advance(self, last_descender)
        container.advance(advance)
        if - descender > container.remaining_height:
            raise EndOfContainer

        # replace tabs with spacers or fillers
        #items = expand_tabs(self) if self._has_tab else self

        # horizontal displacement
        left = self.indent

        if self._has_tab or justification == BOTH and last_line:
            justification = LEFT
        extra_space = self.width - self._cursor
        if justification == BOTH:
            # TODO: padding added to spaces should be prop. to font size
            nr_spaces = sum(len(glyph_span.space_indices)
                            for glyph_span in self)
            add_to_spaces = extra_space / nr_spaces
            for glyph_span in self:
                space_glyph, space_width = glyph_span.space_glyph_and_width
                space_width += add_to_spaces
                glyph_span.space_glyph_and_width = space_glyph, space_width
        elif justification == CENTER:
            left += extra_space / 2.0
        elif justification == RIGHT:
            left += extra_space

        for glyph_span in self:
            y_offset = glyph_span.span.y_offset
            top = container.cursor - y_offset
            space = (glyph_span.space_glyph_and_width, )
            sg = container.canvas.show_glyphs(left, top, glyph_span.span)
            for index, glyphs_and_widths in enumerate(glyph_span):
                if index in glyph_span.space_indices:
                    left += sg.send(space)
                left += sg.send(glyphs_and_widths)
            if len(glyph_span) in glyph_span.space_indices:
                left += sg.send(space)
            sg.close()
        container.advance(- descender)
        return descender


# utility functions

def expand_tabs(items):
    """Generator expanding all :class:`Tab`s in `items`.
    Non-tab items are yielded as is."""
    for item in items:
        if isinstance(item, Tab):
            for element in item.expand():
                yield element
        else:
            yield item
