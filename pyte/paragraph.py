
import itertools
import os

from warnings import warn

from .dimension import Dimension
from .hyphenator import Hyphenator
from .flowable import Flowable, FlowableStyle
from .layout import EndOfContainer
from .reference import LateEval
from .style import ParentStyle
from .text import Character, Space, Box, ControlCharacter, NewLine, Tab, Spacer
from .text import TextStyle, StyledText, MixedStyledText
from .unit import pt


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
    attributes = {'indentLeft': 0*pt,
                  'indentRight': 0*pt,
                  'indentFirst': 0*pt,
                  'lineSpacing': STANDARD,
                  'justify': BOTH,
                  'tab_stops': []}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


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
        self._in_tab = None
        self.current_style = None

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
            cursor = self.text_width
            tab_stop, tab_position = self._find_tab_stop(cursor)
            if tab_stop:
                item.tab_stop = tab_stop
                width = item.tab_width = tab_position - cursor
                if tab_stop.align in (RIGHT, CENTER):
                    self._in_tab = item
                else:
                    self._in_tab = None
        elif self._in_tab and self._in_tab.tab_stop.align == RIGHT:
            if self._in_tab.tab_width <= width:
                try:
                    for first, second in item.hyphenate():
                        first_width = first.width
                        if self._in_tab.tab_width >= first_width:
                            self._in_tab.tab_width -= first_width
                            super().append(first)
                            raise EndOfLine(second)
                except AttributeError:
                    pass
                raise EndOfLine
            else:
                self._in_tab.tab_width -= width
                self.text_width -= width
        elif self._in_tab and self._in_tab.tab_stop.align == CENTER:
            if self._in_tab.tab_width <= width:
                try:
                    for first, second in item.hyphenate():
                        first_width = first.width
                        if self._in_tab.tab_width >= first_width / 2:
                            self._in_tab.tab_width -= first_width / 2
                            super().append(first)
                            raise EndOfLine(second)
                except AttributeError:
                    pass
                raise EndOfLine
            else:
                self._in_tab.tab_width -= width / 2
                self.text_width -= width / 2
        elif self.text_width + width > self.width:
            if len(self) == 0:
                warn('item too long to fit on line')
            else:
                try:
                    for first, second in item.hyphenate():
                        if self.text_width + first.width < self.width:
                            self.append(first)
                            raise EndOfLine(second)
                except AttributeError:
                    pass
                raise EndOfLine

        self.text_width += width
        super().append(item)

    def typeset(self, canvas, last_line=False):
        """Typeset words on the current coordinates"""
        chars = []
        char_widths = []
        max_font_size = 0
        justify = self.paragraph.get_style('justify')
        if Tab in map(type, self) or justify == BOTH and last_line:
            justification = LEFT
        else:
            justification = justify

        # drop spaces at the end of the line
        while isinstance(self[-1], Space):
            self.pop()

        # replace tabs with spacers or fillers
        # TODO: encapsulate (Tab.expand method)
        i = 0
        while i < len(self):
            if isinstance(self[i], Tab):
                tab = self.pop(i)
                try:
                    fill_char = StyledText(tab.tab_stop.fill)
                    fill_char.parent = tab.parent
                    number, rest = divmod(tab.tab_width, fill_char.width)
                    spacer = Spacer(rest)
                    spacer.parent = tab.parent
                    self.insert(i, spacer)
                    fill_text = StyledText(tab.tab_stop.fill * int(number))
                    fill_text.parent = tab.parent
                    self.insert(i + 1, fill_text)
                    i += 1
                except (AttributeError, TypeError):
                    spacer = Spacer(tab.tab_width)
                    spacer.parent = tab.parent
                    self.insert(i, spacer)
            i += 1

        line_width = sum(item.width for item in self)
        max_font_size = max(float(item.height) for item in self)

        extra_space = self.width - line_width

        def _is_scalable_space(item):
            return isinstance(item, Space) and not item.fixed_width

        # horizontal displacement
        x = self.indent
        add_to_spaces = 0.0
        if justification == CENTER:
            x += extra_space / 2.0
        elif justification == RIGHT:
            x += extra_space
        elif justification == BOTH:
            number_of_spaces = list(map(_is_scalable_space, self)).count(True)
            if number_of_spaces:
                add_to_spaces = extra_space / number_of_spaces

        # position cursor
        self.paragraph.newline(max_font_size)

        def typeset_span(item, glyphs, widths):
            font = item.get_font()
            font_size = float(item.height)
            canvas.move_to(x, self.paragraph._line_cursor + item.y_offset)
            canvas.select_font(font, font_size)
            canvas.show_glyphs(glyphs, widths)
            return sum(widths)

        for item in self:
            if isinstance(item, Box):
                x += item.render(canvas, x, self.paragraph._line_cursor)
                continue
            if _is_scalable_space(item):
                widths = [item.widths[0] + add_to_spaces]
            else:
                widths = item.widths
            glyphs = item.glyphs()
            x += typeset_span(item, glyphs, widths)

        return max_font_size


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

    def _split_words(self, spans):
        join = False
        words = []
        for span in spans:
            words += span.split()
        return words

    def render(self, canvas, offset=0):
        return self.typeset(canvas, offset)

    def typeset(self, canvas, offset=0):
        if not self._words:
            self._words = self._split_words(self.spans())

        indent_left = float(self.get_style('indentLeft'))
        indent_right = float(self.get_style('indentRight'))
        indent_first = float(self.get_style('indentFirst'))
        line_width = canvas.width - indent_right

        self._line_cursor = canvas.height - offset
        line_pointers = self.word_pointer, self.field_pointer
        if self.first_line:
            line = Line(self, line_width, indent_left + indent_first)
        else:
            line = Line(self, line_width, indent_left)

        while self.word_pointer < len(self._words):
            word = self._words[self.word_pointer]
            if isinstance(word, LateEval):
                if self.field_pointer is None:
                    self._field_words = self._split_words(word.spans())
                    self.field_pointer = 0
                else:
                    self.field_pointer += 1
                if self._field_words:
                    word = self._field_words[self.field_pointer]
                if self.field_pointer >= len(self._field_words) - 1:
                    self.field_pointer = None
                    self.word_pointer += 1
                if not self._field_words:
                    continue
            else:
                self.word_pointer += 1

            if isinstance(word, (NewLine, Flowable)):
                line_pointers = self.typeset_line(canvas, line, line_pointers,
                                                  last_line=True)
                if isinstance(word, Flowable):
                    # TODO: handle continued flowables
                    flowable_offset = canvas.height - self._line_cursor
                    flowable_height = word.flow(self.container, flowable_offset)
                    self.newline(flowable_height)
                line = Line(self, line_width, indent_left)
            else:
                try:
                    line.append(word)
                except EndOfLine as eol:
                    line_pointers = self.typeset_line(canvas, line,
                                                      line_pointers)
                    line = Line(self, line_width, indent_left)
                    if eol.hyphenation_remainder:
                        line.append(eol.hyphenation_remainder)
                    else:
                        line.append(word)

        # the last line
        if len(line) != 0:
            self.typeset_line(canvas, line, line_pointers, last_line=True)

        self._init_state()
        return canvas.height - offset - self._line_cursor

    def _line_spacing(self, line_height):
        line_spacing = self.get_style('lineSpacing')
        if isinstance(line_spacing, Dimension):
            return float(line_spacing)
        else:
            return line_spacing * line_height

    def typeset_line(self, canvas, line, line_pointers, last_line=False):
        buffer = canvas.new(0, 0, canvas.width, canvas.height)
        try:
            line_height = line.typeset(buffer, last_line)
            self.advance(self._line_spacing(line_height) - line_height)
            canvas.append(buffer)
            try:
                line_pointers = (self.word_pointer - 1, self.field_pointer - 1)
            except TypeError:
                line_pointers = (self.word_pointer - 1, self.field_pointer)
        except EndOfContainer:
            self.word_pointer, self.field_pointer = line_pointers
            raise
        finally:
            del buffer
        self.first_line = False
        return line_pointers

    def newline(self, line_height):
        """Move the cursor downwards by `line_height`"""
        self.advance(line_height)

    def advance(self, space):
        """Advance the line cursor downward by `space`"""
        self._line_cursor -= space

        if self._line_cursor < 0:
            raise EndOfContainer
