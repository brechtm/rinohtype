"""
Classes for representing paragraphs and typesetting them:

* :class:`Paragraph`:
* :class:`ParagraphStyle`:
* :class:`TabStop`:

The line spacing option in a :class:`ParagraphStyle` can be any of:

* :class:`ProportionalSpacing`:
* :class:`FixedSpacing`:
* :class:`Leading`:
* :const:`STANDARD`:
* :const:`SINGLE`:
* :const:`DOUBLE`:

Horizontal justification of the can be:

* :const:`LEFT`
* :const:`RIGHT`
* :const:`CENTER`
* :const:`BOTH`


"""

from itertools import chain, tee

from .dimension import Dimension, PT
from .flowable import FlowableException, Flowable, FlowableStyle
from .hyphenator import Hyphenator
from .layout import DownExpandingContainer, EndOfContainer
from .reference import FieldException, Footnote
from .text import Space, Tab, Spacer
from .text import NewlineException, TabException, TabSpaceExceeded
from .text import TextStyle, MixedStyledText


__all__ = ['']


# Text justification

LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'
BOTH = 'justify'


# Line spacing

class LineSpacing(object):
    """Base class for line spacing types. Line spacing is defined as the
    distance between the baselines of two consecutive lines."""

    def pitch(self, line_height):
        """Return the distance between the baselines of two successive lines."""
        raise NotImplementedError


class ProportionalSpacing(LineSpacing):
    """Line spacing proportional to the line height."""

    def __init__(self, factor):
        """`factor` specifies the amount by which the line height is multiplied
        to obtain the line spacing."""
        self.factor = factor

    def pitch(self, line_height):
        return self.factor * line_height


STANDARD = ProportionalSpacing(1.2)
"""Line spacing of 1.2 times the line height."""


SINGLE = ProportionalSpacing(1.0)
"""Line spacing equal to the line height (no leading)."""


DOUBLE = ProportionalSpacing(2.0)
"""Line spacing of double the line height."""


class FixedSpacing(LineSpacing):
    """Fixed line spacing, with optional minimum spacing."""

    def __init__(self, pitch, minimum=STANDARD):
        """`pitch` specifies the distance between two consecutive lines.
        Optionally, `minimum` specifies the minimum :class:`LineSpacing` to use,
        which can prevent lines with large fonts from overlapping. If no minimum
        is required, set to `None`."""
        self._pitch = float(pitch)
        self.minimum = minimum

    def pitch(self, line_height):
        if self.minimum:
            return max(self._pitch, self.minimum.pitch(line_height))
        else:
            return self._pitch


class Leading(LineSpacing):
    """Line spacing determined by the space in between two lines."""

    def __init__(self, leading):
        """`leading` specifies the space between the bottom on a line and the
        top of the following line."""
        self.leading = leading

    def pitch(self, line_height):
        return float(line_height + self.leading)


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
                  'line_spacing': STANDARD,
                  'justify': BOTH,
                  'tab_stops': []}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Paragraph(MixedStyledText, Flowable):
    """A paragraph of mixed-styled text that can be flowed into a
    :class:`Container`."""

    style_class = ParagraphStyle

    spans = Flowable.spans

    def __init__(self, text_or_items, style=None):
        """"""
        super().__init__(text_or_items, style=style)
        """See :class:`MixedStyledText`. As a paragraph typically doesn't have
        a parent, `style` should be specified."""
        self._init_state()

    def _init_state(self):
        """Prepare this paragraph's state for typesetting."""
        # self._words is an iterator yielding the (remainding) words or other
        # in-line items to typeset.
        self._words = split_into_words(MixedStyledText.spans(self))
        self.first_line = True

    def render(self, container):
        """Typeset the paragraph onto `container`, starting below the current
        cursor position of the container. When the end of the container is
        reached, the rendering state is preserved to continue setting the rest
        of the paragraph when this method is called with a new container."""
        indent_left = float(self.get_style('indent_left'))
        indent_right = float(self.get_style('indent_right'))
        indent_first = float(self.get_style('indent_first'))
        line_spacing = self.get_style('line_spacing')
        justification = self.get_style('justify')
        tab_stops = self.get_style('tab_stops')

        line_width = float(container.width - indent_right)
        first_line_indent = indent_left
        if self.first_line:
            first_line_indent += indent_first
            self.first_line = False

        def typeset_line(line, words, last_line=False):
            """Typeset `line` and, if succesful, update the paragraph's internal
            rendering state. Additionally, this function advances the
            container's pointer downwards the size of the interline spacing."""
            line_height = line.typeset(container, justification, last_line)
            self._words, words = tee(words)
            container.advance(line_spacing.pitch(line_height) - line_height)
            return words

        start_offset = container.cursor
        line = Line(tab_stops, line_width, first_line_indent)
        # self._words is updated after successfully rendering each line, so that
        # when `container` overflows on rendering a line, the words in that line
        # can still be set on the next typeset() call.
        self._words, words = tee(self._words)
        while True:
            try:
                word = next(words)              # throws StopIteration
                spillover = line.append(word)   # throws the other exceptions
                if spillover:
                    words = typeset_line(line, chain((spillover, ), words))
                    line = Line(tab_stops, line_width, indent_left)
            except NewlineException:
                words = typeset_line(line, words, last_line=True)
                line = Line(tab_stops, line_width, indent_left)
            except FieldException:
                field_words = split_into_words(word.field_spans(container))
                words = chain(field_words, words)
            except FlowableException:
                words = typeset_line(line, words, last_line=True)
                child_container = DownExpandingContainer(container,
                                                         left=indent_left,
                                                         top=container.cursor)
                container.advance(word.flow(child_container))
                line = Line(tab_stops, line_width, indent_left)
            except StopIteration:
                if line:
                    typeset_line(line, words, last_line=True)
                break

        self._init_state()  # reset the state for the next rendering pass
        return container.cursor - start_offset


class Line(list):
    """Helper class for building and typesetting a single line of text within
    a :class:`Paragraph`."""

    def __init__(self, tab_stops, width, indent):
        """`tab_stops` is a list of tab stops, as given in the paragraph style.
        `width` is the available line width.
        `indent` specifies the left indent width."""
        super().__init__()
        self.tab_stops = tab_stops
        self.width = width
        self.indent = indent
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
                    item.warn('item too long to fit on line')
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
            item.warn('Tab space exceeded.')
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
            tab.warn('No tab stops defined for this paragraph style.')
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

    def typeset(self, container, justification, last_line=False):
        """Typeset the line at the onto `container` below its current cursor
        position. `justification` is passed on from the paragraph style and
        `last_line` specifies whether this is the last line of the paragraph.
        Returns the line's height."""
        try:
            # drop spaces at the end of the line
            while isinstance(self[-1], Space):
                self._cursor -= self.pop().width
        except IndexError:
            return 0

        line_height = max(float(item.height) for item in self)
        container.advance(line_height)

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
                if span: span.close()
                font, size, y_offset = font_style
                top = container.cursor - y_offset
                span = container.canvas.show_glyphs(left, top, font, size)
            left += span.send(zip(item.glyphs(), item.widths()))
            prev_font_style = font_style
        span.close()

        return line_height


# utility functions

def split_into_words(spans):
    for span in spans:
        try:
            for part in span.split():
                yield part
        except AttributeError:
            yield span


def expand_tabs(items):
    for item in items:
        if isinstance(item, Tab):
            for element in item.expand():
                yield element
        else:
            yield item


def stretch_spaces(items, add_to_spaces):
    for item in items:
        if type(item) is Space:
            yield Spacer(item.width + add_to_spaces,
                         style=item.style, parent=item.parent)
        else:
            yield item
