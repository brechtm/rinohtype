
from itertools import chain, tee

from .dimension import Dimension, PT
from .hyphenator import Hyphenator
from .flowable import FlowableException, Flowable, FlowableStyle
from .layout import DownExpandingContainer, EndOfContainer
from .reference import FieldException, Footnote
from .text import Space, NewlineException, Tab, TabException, Spacer
from .text import TextStyle, MixedStyledText


# Text justification
LEFT = 'left'
RIGHT = 'right'
CENTER = 'center'
BOTH = 'justify'


# Line spacing
STANDARD = 1.2
SINGLE = 1.0
DOUBLE = 2.0

# TODO: LineSpacing class (leading, proportional, exact, at-least, ...)?
##class LineSpacing(object):
##    def __self__(self, leading, proportional, ...):



# TODO: look at Word/OpenOffice for more options
class ParagraphStyle(TextStyle, FlowableStyle):
    attributes = {'indent_left': 0*PT,
                  'indent_right': 0*PT,
                  'indent_first': 0*PT,
                  'line_spacing': STANDARD,
                  'justify': BOTH,
                  'tab_stops': []}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TabStop(object):
    def __init__(self, position, align=LEFT, fill=None):
        self._position = position
        self.align = align
        self.fill = fill

    def get_position(self, width):
        if isinstance(self._position, Dimension):
            return float(self._position)
        else:
            return width * self._position


class Line(list):
    def __init__(self, tab_stops, width, indent=0.0):
        super().__init__()
        self.tab_stops = tab_stops
        self.width = width - indent
        self.indent = indent
        self.text_width = 0
        self.has_tab = False
        self._current_tab = None

    def _first_append(self, item):
        if not isinstance(item, Space):
            self.append = self._normal_append
            return self.append(item)

    append = _first_append

    def _normal_append(self, item):
        try:
            width = item.width
            if self.text_width + width > self.width:
                for first, second in item.hyphenate():
                    if self.text_width + first.width < self.width:
                        self.text_width += first.width
                        super().append(first)
                        return second
                if not self:
                    item.warn('item too long to fit on line')
                else:
                    return item
        except TabException:
            self.has_tab = True
            width = self._handle_tab(item)
        self.text_width += width
        super().append(item)

    def _tab_append(self, item):
        try:
            factor = 2 if self._current_tab.tab_stop.align == CENTER else 1
            width = item.width / factor
            if self._current_tab.tab_width <= width:
                for first, second in item.hyphenate():
                    first_width = first.width / factor
                    if self._current_tab.tab_width >= first_width:
                        self._current_tab.tab_width -= first_width
                        super().append(first)
                        return second
                return item
            else:
                self._current_tab.tab_width -= width
        except TabException:
            width = self._handle_tab(item)
        self.text_width += width
        super().append(item)

    def _handle_tab(self, tab):
        for tab_stop in self.tab_stops:
            tab_position = tab_stop.get_position(self.width)
            if self.text_width < tab_position:
                tab.tab_stop = tab_stop
                tab.tab_width = tab_position - self.text_width
                if tab_stop.align in (RIGHT, CENTER):
                    self._current_tab = tab
                    self.append = self._tab_append
                else:
                    self._current_tab = None
                    self.append = self._normal_append
                return tab.tab_width

    def typeset(self, container, justification, last_line=False):
        """Typeset words at the current coordinates"""
        if self.has_tab or justification == BOTH and last_line:
            justification = LEFT

        # drop spaces at the end of the line
        try:
            while isinstance(self[-1], Space):
                self.text_width -= self.pop().width
        except IndexError:
            return 0

        # replace tabs with spacers or fillers
        items = expand_tabs(self) if self.has_tab else self

        # horizontal displacement
        x = self.indent

        extra_space = self.width - self.text_width
        if justification == BOTH:
            number_of_spaces = sum(1 for item in self if type(item) is Space)
            if number_of_spaces:
                items = stretch_spaces(items, extra_space / number_of_spaces)
            # TODO: padding added to spaces should be prop. to font size
        elif justification == CENTER:
            x += extra_space / 2.0
        elif justification == RIGHT:
            x += extra_space

        # position cursor
        line_height = max(float(item.height) for item in self)
        container.advance(line_height)

        span = None
        prev_font_style = None
        for item in items:
            font_style = font, size, y_offset = item.font, float(item.height), item.y_offset
            if font_style != prev_font_style:
                if span: span.close()
                span = container.canvas.show_glyphs(x, container.cursor - y_offset, font, size)
                next(span)
            x += span.send(zip(item.glyphs(), item.widths()))
            prev_font_style = font_style
        span.close()

        return line_height


class Paragraph(MixedStyledText, Flowable):
    style_class = ParagraphStyle

    spans = Flowable.spans

    def __init__(self, items, style=None):
        super().__init__(items, style=style)
        # TODO: move to TextStyle
        #self.char_spacing = 0.0
        self._init_state()

    def _init_state(self):
        self._words = split_into_words(MixedStyledText.spans(self))
        self.first_line = True

    def render(self, container):
        return self.typeset(container)

    def typeset(self, container):
        start_offset = container.cursor

        justification = self.get_style('justify')
        tab_stops = self.get_style('tab_stops')
        indent_left = float(self.get_style('indent_left'))
        indent_right = float(self.get_style('indent_right'))
        indent_first = float(self.get_style('indent_first'))
        line_width = float(container.width - indent_right)
        first_line_indent = indent_left
        if self.first_line:
            first_line_indent += indent_first
            self.first_line = False

        def typeset_line(line, words, last_line=False):
            line_height = line.typeset(container, justification, last_line)
            container.advance(self._line_spacing(line_height) - line_height)
            self._words, words = tee(words)
            return words

        line = Line(tab_stops, line_width, first_line_indent)
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

        self._init_state()
        return container.cursor - start_offset

    def _line_spacing(self, line_height):
        line_spacing = self.get_style('line_spacing')
        if isinstance(line_spacing, Dimension):
            return float(line_spacing)
        else:
            return line_spacing * line_height


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
