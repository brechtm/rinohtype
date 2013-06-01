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

from collections import namedtuple
from copy import copy
from itertools import chain, tee

from .dimension import Dimension, PT
from .flowable import FlowableException, Flowable, FlowableStyle, FlowableState
from .layout import DownExpandingContainer, EndOfContainer
from .reference import FieldException
from .text import Space, Tab, Spacer
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
        max_line_gap = max(float(item.line_gap) for item in line)
        ascender = max(float(item.ascender) for item in line)
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
        max_font_size = max(float(item.height) for item in line)
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

    * `indent_left`: Left indentation of text (class:`Dimension`).
    * `indent_right`: Right indentation of text (class:`Dimension`).
    * `indent_first`: Indentation of the first line of text (class:`Dimension`).
    * `line_spacing`: Spacing between the baselines of two successive lines of
                      text (:class:`LineSpacing`).
    * `justify`: Alignment of the text to the margins (:const:`LEFT`,
                 :const:`RIGHT`, :const:`CENTER` or :const:`BOTH`).
    * `tab_stops`: The tab stops for this paragraph (list of :class:`TabStop`).
    """

    attributes = {'indent_left': 0*PT,
                  'indent_right': 0*PT,
                  'indent_first': 0*PT,
                  'line_spacing': DEFAULT,
                  'justify': BOTH,
                  'tab_stops': []}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class ParagraphState(FlowableState):
    def __init__(self, items, first_line=True, nested_flowable_state=None):
        self.items = items
        self.first_line = first_line
        self.nested_flowable_state = nested_flowable_state

    def __copy__(self):
        self.items, copy_items = tee(self.items)
        copy_nested_flowable_state = copy(self.nested_flowable_state)
        return self.__class__(copy_items, self.first_line,
                              copy_nested_flowable_state)

    def next_item(self):
        return next(self.items)

    def prepend(self, item):
        self.items = chain((item, ), self.items)


class Paragraph(MixedStyledText, Flowable):
    """A paragraph of mixed-styled text that can be flowed into a
    :class:`Container`."""

    style_class = ParagraphStyle

    spans = Flowable.spans

    def __init__(self, text_or_items, style=None):
        """See :class:`MixedStyledText`. As a paragraph typically doesn't have
        a parent, `style` should be specified."""
        super().__init__(text_or_items, style=style)

    def initial_state(self):
        """Return the initial rendering state for this paragraph."""
        return ParagraphState(split_into_words(MixedStyledText.spans(self)))

    def render(self, container, descender, state=None):
        """Typeset the paragraph onto `container`, starting below the current
        cursor position of the container. `descender` is the descender height of
        the preceeding line or `None`.
        When the end of the container is reached, the rendering state is
        preserved to continue setting the rest of the paragraph when this method
        is called with a new container."""
        state = state or self.initial_state()
        indent_left = float(self.get_style('indent_left'))
        indent_right = float(self.get_style('indent_right'))
        indent_first = float(self.get_style('indent_first'))
        line_spacing = self.get_style('line_spacing')
        justification = self.get_style('justify')
        tab_stops = self.get_style('tab_stops')

        line_width = float(container.width - indent_right)
        first_line_indent = indent_left
        if state.first_line:
            first_line_indent += indent_first
            state.first_line = False

        # `saved_state` is updated after successfully rendering each line, so that
        # when `container` overflows on rendering a line, the words in that line
        # are yielded again on the next typeset() call.
        saved_state = copy(state)

        def typeset_line(line, last_line=False):
            """Typeset `line` and, if no exception is raised, update the
            paragraph's internal rendering state."""
            nonlocal saved_state, state, descender
            try:
                descender = line.typeset(container, justification, line_spacing,
                                         descender, last_line)
                saved_state = copy(state)
            except EndOfContainer as e:
                raise EndOfContainer(saved_state)

        def render_nested_flowable(flowable):
            nonlocal state, descender
            max_height = float(container.remaining_height)
            # FIXME: trouble if `container` is an ExpandingContainer
            nested_container = DownExpandingContainer(container,
                                                      left=indent_left,
                                                      top=container.cursor,
                                                      max_height=max_height)
            try:
                height, descender = flowable.flow(nested_container, descender,
                                                  state.nested_flowable_state)
                state.nested_flowable_state = None
                container.advance(height)
                line = Line(tab_stops, line_width, indent_left, container)
            except EndOfContainer as e:
                state.prepend(flowable)
                state.nested_flowable_state = e.flowable_state
                raise EndOfContainer(state)

        line = Line(tab_stops, line_width, first_line_indent, container)
        while True:
            try:
                word = state.next_item()        # throws StopIteration
                spillover = line.append(word)   # throws the other exceptions
                if spillover:
                    state.prepend(spillover)
                    typeset_line(line)
                    line = Line(tab_stops, line_width, indent_left, container)
            except NewlineException:
                typeset_line(line, last_line=True)
                line = Line(tab_stops, line_width, indent_left, container)
            except FieldException:
                field_words = split_into_words(word.field_spans(container))
                state.items = chain(field_words, state.items)
            except FlowableException:
                typeset_line(line, last_line=True)
                render_nested_flowable(word)
            except StopIteration:
                if line:
                    typeset_line(line, last_line=True)
                break

        return descender


class Line(list):
    """Helper class for building and typesetting a single line of text within
    a :class:`Paragraph`."""

    def __init__(self, tab_stops, width, indent, container):
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

    # Line is a simple state machine. Different methods are assigned to
    # Line.append, depending on the current state.

    def _empty_append(self, item):
        """Append method used when the line is still empty. Discards `item` if
        it is a space (:class:`Space` and subclasses)."""
        if not isinstance(item, Space):
            self.append = self._normal_append
            return self.append(item)

    append = _empty_append

    def _normal_append(self, item):
        """Appends `item` to this line. If the item doesn't fit on the line,
        returns the spillover. Otherwise returns `None`."""
        try:
            width = item.width
            if self._cursor + width > self.width:
                for first, second in item.hyphenate():
                    if self._cursor + first.width < self.width:
                        self._cursor += first.width
                        super().append(first)
                        return second
                if not self:
                    item.warn('item too long to fit on line', self.container)
                else:
                    return item
        except TabException:
            self._has_tab = True
            width, item = self._handle_tab(item)
        self._cursor += width
        super().append(item)

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

    def typeset(self, container, justification, line_spacing, last_descender,
                last_line=False):
        """Typeset the line at into `container` below its current cursor
        position. Advances the container's cursor to below the descender of this
        line.

        `justification` and `line_spacing` are passed on from the
        paragraph style. `last_descender` is the last line's descender, used in
        the vertical positioning of this line. Finally, `last_line` specifies
        whether this is the last line of the paragraph.

        Returns the line's descender size."""
        try:
            # drop spaces at the end of the line
            while isinstance(self[-1], Space):
                self._cursor -= self.pop().width
        except IndexError:
            return last_descender

        descender = min(float(item.descender) for item in self)

        if last_descender is None:
            advance = max(float(item.ascender) for item in self)
        else:
            advance = line_spacing.advance(self, last_descender)
        container.advance(advance)
        if - descender > container.remaining_height:
            raise EndOfContainer

        # replace tabs with spacers or fillers
        items = expand_tabs(self) if self._has_tab else self

        # horizontal displacement
        left = self.indent

        if self._has_tab or justification == BOTH and last_line:
            justification = LEFT
        extra_space = self.width - self._cursor
        if justification == BOTH:
            number_of_spaces = sum(1 for item in self if type(item) is Space)
            if number_of_spaces:
                # TODO: padding added to spaces should be prop. to font size
                items = stretch_spaces(items, extra_space / number_of_spaces)
        elif justification == CENTER:
            left += extra_space / 2.0
        elif justification == RIGHT:
            left += extra_space

        span = None
        prev_font_style = None
        for item in items:
            font_style = item.font, float(item.height), item.y_offset
            if font_style != prev_font_style:
                if span:
                    span.close()
                font, size, y_offset = font_style
                top = container.cursor - y_offset
                span = container.canvas.show_glyphs(left, top, font, size)
            left += span.send(zip(item.glyphs(), item.widths()))
            prev_font_style = font_style
        span.close()
        container.advance(- descender)
        return descender


# utility functions

def split_into_words(spans):
    """Generator yielding all words in `spans`.
    Spans in `span` that do not have a split() method are yielded as is."""
    for span in spans:
        try:
            for part in span.split():
                yield part
        except AttributeError:
            yield span


def expand_tabs(items):
    """Generator expanding all :class:`Tab`s in `items`.
    Non-tab items are yielded as is."""
    for item in items:
        if isinstance(item, Tab):
            for element in item.expand():
                yield element
        else:
            yield item


def stretch_spaces(items, add_to_spaces):
    """Generator replacing all :class:`Space`s with :class:`Spacer`s with a with
    equal to that of a space plus `add_to_spaces`.
    Non-spaces are yielded as is."""
    for item in items:
        if type(item) is Space:
            yield Spacer(item.width + add_to_spaces,
                         style=item.style, parent=item.parent)
        else:
            yield item
