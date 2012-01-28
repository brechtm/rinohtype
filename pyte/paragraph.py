
import itertools
import os

from warnings import warn

from .dimension import Dimension
from .hyphenator import Hyphenator
from .flowable import Flowable, FlowableStyle
from .layout import EndOfContainer
from .text import Character, Space, Box, ControlCharacter, NewLine, Tab
from .text import TextStyle, MixedStyledText
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
        self.position = position
        self.align = align
        self.fill = fill


class Word(list):
    def __init__(self, characters, kerning, ligatures):
        super().__init__()
        self.kerning = kerning
        self.ligatures = ligatures
        self.hyphen_enable = True
        self.hyphen_chars = 0
        self.hyphen_lang = None
        for char in characters:
            self.append(char)

    stringwidth = None
    font_size = None

    def __repr__(self):
        return ''.join([char.text for char in self])

    def __getitem__(self, index):
        result = super().__getitem__(index)
        if type(index) == slice:
            result = __class__(result, self.kerning, self.ligatures)
        return result

    def append(self, char):
        if isinstance(char, Character):
            if self.hyphen_enable:
                self.hyphen_enable = char.get_style('hyphenate')
                self.hyphen_chars = max(self.hyphen_chars,
                                        char.get_style('hyphenChars'))
                if self.hyphen_lang is None:
                    self.hyphen_lang = char.get_style('hyphenLang')
                elif char.get_style('hyphenLang') != self.hyphen_lang:
                    self.hyphen_enable = False
        elif isinstance(char, Box):
            # TODO: should a Box even be a part of a Word?
            import pdb; pdb.set_trace()
            pass
        else:
            raise ValueError('expecting Character or Box')
        super().append(char)

    def substitute_ligatures(self):
        if self.ligatures:
            i = 0
            while i + 1 < len(self):
                character = self[i]
                next_character = self[i + 1]
                try:
                    self[i] = character.ligature(next_character)
                    del self[i + 1]
                except TypeError:
                    i += 1

    @property
    def width(self):
        width = 0.0
        for i, character in enumerate(self):
            if isinstance(character, Box):
                width += character.width
            else:
                if self.stringwidth is None or character.new_span:
                    self.font_metrics = character.get_font().psFont.metrics
                    self.stringwidth = self.font_metrics.stringwidth
                    self.font_size = float(character.get_style('fontSize'))

                width += self.stringwidth(character.text, self.font_size)
                if self.kerning:
                    width += self.kern(i)
        return width

    def kern(self, index):
        if not self.kerning or index == len(self) - 1:
            kerning = 0.0
        else:
            this_char = self[index]
            next_char = self[index + 1]
            try:
                kern = this_char.kerning(next_char)
                kerning = kern * float(self.font_size) / 1000.0
            except TypeError:
                kerning = 0.0

        return kerning

    dic_dir = os.path.join(os.path.dirname(__file__), 'data', 'hyphen')

    def hyphenate(self):
        if not self.hyphen_enable:
            return

        dic_path = dic_file = 'hyph_{}.dic'.format(self.hyphen_lang)
        if not os.path.exists(dic_path):
            dic_path = os.path.join(self.dic_dir, dic_file)
            if not os.path.exists(dic_path):
                raise IOError("Hyphenation dictionary '{}' neither found in "
                              "current directory, nor in the data directory"
                              .format(dic_file))

        word = str(self)
        h = Hyphenator(dic_path, self.hyphen_chars, self.hyphen_chars)
        for position in reversed(h.positions(word)):
            parts = h.wrap(word, position + 1)
            if "".join((parts[0][:-1], parts[1])) != word:
                raise NotImplementedError
            first, second = self[:position], self[position:]
            hyphen = Character('-', style=first[-1].style)
            hyphen.parent = first[-1].parent
            first.append(hyphen)
            yield first, second


class Field(object):
    def __init__(self, source):
        self.source = source

    def characters(self):
        for character in self.source.field_characters():
            yield character


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

    def _find_tab_stop(self, cursor):
        for tab_stop in self.paragraph.get_style('tab_stops'):
            if cursor < tab_stop.position:
                return tab_stop

    def append(self, item):
        try:
            # TODO: keep non-ligatured version in case word doesn't fit on line
            item.substitute_ligatures()
        except AttributeError:
            pass
        width = item.width

        if isinstance(item, Space):
            if len(self) == 0:
                return
        elif isinstance(item, Tab):
            cursor = self.indent + self.text_width
            tab_stop = self._find_tab_stop(cursor)
            if tab_stop:
                item.tab_width = float(tab_stop.position) - cursor
                self.text_width = float(tab_stop.position) - self.indent
        elif self.text_width + width > self.width:
            if len(self) == 0:
                warn('item too long to fit on line')
            else:
                try:
                    for first, second in item.hyphenate():
                        first_width = first.width
                        if self.text_width + first_width < self.width:
                            self.text_width += first_width
                            super().append(first)
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
        x_offset = 0
        max_font_size = 0
        justify = self.paragraph.get_style('justify')
        if Tab in map(type, self) or justify == BOTH and last_line:
            justification = LEFT
        else:
            justification = justify
        while isinstance(self[-1], Space):
            self.pop()

        # calculate total width of all characters (excluding spaces)
        for word in self:
            if isinstance(word, Space):
                if justification != BOTH or word.fixed_width:
                    chars.append(word)
                    char_widths.append(word.width)
                else:
                    chars.append(word)
                    char_widths.append(0.0)
            elif isinstance(word, Tab):
                chars.append(word)
                char_widths.append(word.tab_width)
            else:
                for j, character in enumerate(word):
                    current_font_size = float(character.height)
                    max_font_size = max(current_font_size, max_font_size)
                    kerning = word.kern(j)
                    chars.append(character)
                    char_widths.append(character.width + kerning) #+ spacing

        line_width = sum(char_widths)

        # calculate space width
        if justification == BOTH:
            try:
                def is_scalable_space(item):
                    return isinstance(item, Space) and not item.fixed_width
                number_of_spaces = list(map(is_scalable_space, self)).count(True)
                space_width = (self.width - line_width) / (number_of_spaces)
            except ZeroDivisionError:
                space_width = 0.0
            for i, char in enumerate(chars):
                if isinstance(char, Space) and not char.fixed_width:
                    char_widths[i] = space_width
        else:
            extra_space = self.width - line_width

        # horizontal displacement
        x = self.indent
        if justification == CENTER:
            x += extra_space / 2.0
        elif justification == RIGHT:
            x += extra_space

        # position cursor
        self.paragraph._line_cursor -= max_font_size
        canvas.move_to(x, self.paragraph._line_cursor)

        if isinstance(chars[0], Character):
            current_style = {'typeface': chars[0].get_style('typeface'),
                             'fontWeight': chars[0].get_style('fontWeight'),
                             'fontSlant': chars[0].get_style('fontSlant'),
                             'fontWidth': chars[0].get_style('fontWidth'),
                             'fontSize': chars[0].get_style('fontSize')}
        else:
            current_style = 'box'

        span_chars = []
        span_char_widths = []
        for i, char in enumerate(chars):
            if isinstance(char, Box):
                if span_chars:
                    x_offset += self.typeset_span(canvas, current_style,
                                                  span_chars, span_char_widths)
                    span_chars = []
                    span_char_widths = []
                    current_style = 'box'
                x_offset += self.typeset_box(canvas, x + x_offset,
                                             self.paragraph._line_cursor, char)
            else:
                char_style = {'typeface': char.get_style('typeface'),
                              'fontWeight': char.get_style('fontWeight'),
                              'fontSlant': char.get_style('fontSlant'),
                              'fontWidth': char.get_style('fontWidth'),
                              'fontSize': char.get_style('fontSize')}
                if current_style == 'box':
                    current_style = char_style
                elif char_style != current_style:
                    x_offset += self.typeset_span(canvas, current_style,
                                                  span_chars, span_char_widths)
                    span_chars = []
                    span_char_widths = []
                    current_style = char_style

                span_chars.append(char.glyph_name)
                span_char_widths.append(char_widths[i])

        if span_chars:
            self.typeset_span(canvas, current_style, span_chars,
                              span_char_widths)

        return max_font_size

    def typeset_span(self, canvas, style, span_chars, span_char_widths):
        """Typeset a series of characters with the same style"""
        font = style['typeface'].get(weight=style['fontWeight'],
                                     slant=style['fontSlant'],
                                     width=style['fontWidth'])
        canvas.select_font(font, float(style['fontSize']))
        canvas.show_glyphs(span_chars, span_char_widths)
        return sum(span_char_widths)

    def typeset_box(self, canvas, x, y, box):
        box_canvas = canvas.append_new(x, y - box.depth, box.width,
                                       box.height + box.depth)
        print(box.ps, file=box_canvas.psg_canvas)
        # TODO: the following is probably not be the best way to do this
        print("( ) [ {} ] xshow".format(box.width), file=canvas.psg_canvas)
        return box.width


class Paragraph(MixedStyledText, Flowable):
    style_class = ParagraphStyle

    def __init__(self, items, style=None):
        super().__init__(items, style=style)
        # TODO: move to TextStyle
        self.kerning = True
        self.ligatures = True
        #self.char_spacing = 0.0

        self._words = []
        self._init_state()

    def _init_state(self):
        self.word_pointer = 0
        self.field_pointer = None
        self.first_line = True

    def _split_words(self, characters):
        group_function = lambda item: isinstance(item, (Space, Field,
                                                        ControlCharacter))
        words = []
        for is_special, item in itertools.groupby(characters, group_function):
            if is_special:
                words += item
            else:
                words.append(Word(item, self.kerning, self.ligatures))
        return words

    def render(self, canvas, offset=0):
        try:
            self._previous_page = self._page
        except AttributeError:
            self._page = canvas.page.number
        return self.typeset(canvas, offset)

    def typeset(self, canvas, offset=0):
        if not self._words:
            self._words = self._split_words(self.characters())

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
            if isinstance(word, Field):
                if self.field_pointer is None:
                    self._field_words = self._split_words(word.characters())
                    self.field_pointer = 0
                else:
                    self.field_pointer += 1
                word = self._field_words[self.field_pointer]
                if self.field_pointer == len(self._field_words) - 1:
                    self.field_pointer = None
                    self.word_pointer += 1
            else:
                self.word_pointer += 1

            if isinstance(word, NewLine):
                line_pointers = self.typeset_line(canvas, line, line_pointers,
                                                  last_line=True)
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
        line_height = line.typeset(buffer, last_line)
        try:
            self.newline(self._line_spacing(line_height) - line_height)
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
