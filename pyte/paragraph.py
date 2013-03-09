
from itertools import tee

from .dimension import Dimension, PT
from .hyphenator import Hyphenator
from .flowable import Flowable, FlowableStyle
from .layout import DownExpandingContainer, EndOfContainer
from .reference import LateEval, Footnote
from .text import Character, Space, Box, Newline, Tab, Spacer
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


class EndOfLine(Exception):
    def __init__(self, hyphenation_remainder=None):
        self.hyphenation_remainder = hyphenation_remainder


class Line(list):
    def __init__(self, paragraph, width, indent=0.0):
        super().__init__()
        self.paragraph = paragraph
        self.width = width - indent
        self.indent = indent
        self.text_width = 0
        self._has_tab = False
        self._in_tab = None

    def _find_tab_stop(self, cursor):
        for tab_stop in self.paragraph.get_style('tab_stops'):
            tab_position = tab_stop.get_position(self.width)
            if cursor < tab_position:
                return tab_stop, tab_position
        else:
            return None, None

    def append(self, item):
        width = item.width
        if not self and isinstance(item, Space):
            return
        elif isinstance(item, Tab):
            self._has_tab = True
            cursor = self.text_width
            tab_stop, tab_position = self._find_tab_stop(cursor)
            if tab_stop:
                item.tab_stop = tab_stop
                width = item.tab_width = tab_position - cursor
                if tab_stop.align in (RIGHT, CENTER):
                    self._in_tab = item
                else:
                    self._in_tab = None
        elif self._in_tab:
            factor = 2 if self._in_tab.tab_stop.align == CENTER else 1
            if self._in_tab.tab_width <= width:
                for first, second in item.hyphenate():
                    first_width = first.width / factor
                    if self._in_tab.tab_width >= first_width:
                        self._in_tab.tab_width -= first_width
                        super().append(first)
                        raise EndOfLine(second)
                raise EndOfLine(item)
            else:
                self._in_tab.tab_width -= width / factor
                self.text_width -= width / factor
        elif self.text_width + width > self.width:
            if len(self) == 0:
                item.warn('item too long to fit on line')
                # TODO: print source location (and repeat for diff. occurences)
            else:
                for first, second in item.hyphenate():
                    if self.text_width + first.width < self.width:
                        self.text_width += first.width
                        super().append(first)
                        raise EndOfLine(second)
                raise EndOfLine(item)

        self.text_width += width
        super().append(item)

    def typeset(self, container, last_line=False):
        """Typeset words at the current coordinates"""
        justification = self.paragraph.get_style('justify')
        if self._has_tab or justification == BOTH and last_line:
            justification = LEFT

        # drop spaces at the end of the line
        try:
            while isinstance(self[-1], Space):
                self.text_width -= self.pop().width
        except IndexError:
            return 0

        # replace tabs with spacers or fillers
        def expand_tabs(items):
            for item in items:
                if isinstance(item, Tab):
                    for element in item.expand():
                        yield element
                else:
                    yield item

        items = expand_tabs(self)

        # horizontal displacement
        x = self.indent

        extra_space = self.width - self.text_width
        if justification == BOTH:
            def stretch_spaces(items, add_to_spaces):
                for item in self:
                    if type(item) is Space:
                        yield Spacer(item.width + add_to_spaces,
                                     style=item.style, parent=item.parent)
                    else:
                        yield item

            number_of_spaces = sum(1 for item in self if type(item) is Space)
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

    def __init__(self, items, style=None):
        super().__init__(items, style=style)
        # TODO: move to TextStyle
        #self.char_spacing = 0.0

        self._words = []
        self._init_state()

    def _init_state(self):
        self.word_pointer = 0
        self.field_pointer = None
        self.first_line = True
        self.spillover = None
        self.word_pointer = self._split_words(self.spans())
        self.remainder = None

    def _split_words(self, spans):
        for span in spans:
            try:
                for part in span.split():
                    yield part
            except AttributeError:
                yield span

    def render(self, container):
        return self.typeset(container)

    def typeset(self, container):
        if not self._words:
            self._words = True
            #self._words = self._split_words(self.spans())
            #self.word_pointer = iter(self._words)
            self.word_pointer = self._split_words(self.spans())

        canvas = container.canvas
        start_offset = container.cursor

        indent_left = float(self.get_style('indent_left'))
        indent_right = float(self.get_style('indent_right'))
        indent_first = float(self.get_style('indent_first'))
        line_width = float(container.width - indent_right)

        self._last_font_style = None
        line_pointers = self.word_pointer, self.field_pointer
        if self.first_line:
            self.first_line = False
            line = Line(self, line_width, indent_left + indent_first)
        else:
            line = Line(self, line_width, indent_left)
        self.word_pointer, self.saved_pointer = tee(self.word_pointer)

        def typeset_line(line, last_line=False):
            try:
                line_height = line.typeset(container, last_line)
                container.advance(self._line_spacing(line_height) - line_height)
            except EndOfContainer:
                self.word_pointer = self.saved_pointer
                raise

        def append(line, word):
            if not line and self.remainder:
                line.append(self.remainder)
            try:
                line.append(word)
            except EndOfLine as eol:
                typeset_line(line)
                self.remainder = eol.hyphenation_remainder
                line = Line(self, line_width, indent_left)
                self.word_pointer, self.saved_pointer = tee(self.word_pointer)
            return line

        for word in self.word_pointer:
            if isinstance(word, LateEval):
                continue
##                if self.field_pointer is None:
##                    self._field_words = self._split_words(word.spans(container))
##                    self.field_pointer = 0
##                else:
##                    self.field_pointer += 1
##                if self._field_words:
##                    word = self._field_words[self.field_pointer]
##                if self.field_pointer >= len(self._field_words) - 1:
##                    self.field_pointer = None
####                    self.word_pointer += 1
##                if not self._field_words:
##                    continue
####            else:
####                self.word_pointer += 1

            if isinstance(word, Flowable):
                typeset_line(line, last_line=True)
                child_container = DownExpandingContainer(container,
                                    left=self.get_style('indent_left'),
                                    top=container.cursor*PT)
                container.advance(word.flow(child_container))
                line = Line(self, line_width, indent_left)
                self.word_pointer, self.saved_pointer = tee(self.word_pointer)
            else:
                line = append(line, word)

        # the last line
        if len(line) != 0:
            typeset_line(line, last_line=True)

        self._init_state()
        return container.cursor - start_offset

    def _line_spacing(self, line_height):
        line_spacing = self.get_style('line_spacing')
        if isinstance(line_spacing, Dimension):
            return float(line_spacing)
        else:
            return line_spacing * line_height
