
import itertools
import os

from psg.drawing.box import canvas
from psg.util.measure import bounding_box
from psg.exceptions import *

from .hyphenator import Hyphenator
from .unit import pt
from .text import Character, Space, Box, NewLine
from .text import TextStyle, MixedStyledText
from .flowable import Flowable, FlowableStyle


class Justify:
    Left = "left"
    Right = "right"
    Center = "center"
    Both = "justify"


# TODO: look at Word/OpenOffice for more options
class ParagraphStyle(TextStyle, FlowableStyle):
    attributes = {'indentLeft': 0*pt,
                  'indentRight': 0*pt,
                  'indentFirst': 0*pt,
                  'lineSpacing': 10*pt, # TODO: change default
                  'justify': Justify.Both}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


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


class EndOfLine(Exception):
    def __init__(self, hyphenation_remainder=None):
        self.hyphenation_remainder = hyphenation_remainder


class Line(list):
    def __init__(self, paragraph, width, indent=0.0):
        super().__init__()
        self.paragraph = paragraph
        self.width = width
        self.indent = indent
        self.text_width = indent

    def append(self, item):
        try:
            # TODO: keep non-ligatured version in case word doesn't fit on line
            item.substitute_ligatures()
        except AttributeError:
            pass
        width = item.width

        if self.text_width + width > self.width:
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
        else:
            self.text_width += width
            super().append(item)

    def typeset(self, pscanvas, last_line=False):
        """Typeset words on the current coordinates"""
        chars = []
        char_widths = []
        x_offset = 0
        max_font_size = 0
        justification = self.paragraph.get_style('justify')

        # calculate total width of all characters (excluding spaces)
        for word in self:
            if isinstance(word, Space):
                if word is not self[-1]:
                    chars.append(word)
                    char_widths.append(0.0)
                    # TODO: handle Spacer
                    #char_widths.append(word.width)
            else:
                for j, character in enumerate(word):
                    current_font_size = float(character.height)
                    max_font_size = max(current_font_size, max_font_size)
                    kerning = word.kern(j)

                    chars.append(character)
                    char_widths.append(character.width + kerning) #+ spacing

        line_width = sum(char_widths)

        # calculate space width
        if justification == "justify" and not last_line:
            try:
                number_of_words = list(map(type, self)).count(Word)
                space_width = (self.width - line_width) / (number_of_words - 1)
            except ZeroDivisionError:
                space_width = 0.0
            for i, char in enumerate(chars):
                if isinstance(char, Space):
                    char_widths[i] = space_width
        else:
            for i, char in enumerate(chars):
                if isinstance(char, Space):
                    char_widths[i] = char.width
                    line_width += char_widths[i]
            extra_space = self.width - line_width

        # horizontal displacement
        x = self.indent
        if justification == "center":
            x += extra_space / 2.0
        elif justification == "right":
            x += extra_space

        # position PostScript's cursor
        self.paragraph._line_cursor -= max_font_size
        print("{0} {1} moveto".format(x, self.paragraph._line_cursor),
              file=pscanvas)

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
                    x_offset += self.typeset_span(pscanvas, current_style,
                                                  span_chars, span_char_widths)
                    span_chars = []
                    span_char_widths = []
                    current_style = 'box'
                x_offset += self.typeset_box(pscanvas, x + x_offset,
                                             self.paragraph._line_cursor, char)
            elif isinstance(char, NewLine):
                pass
            else:
                char_style = {'typeface': char.get_style('typeface'),
                              'fontWeight': char.get_style('fontWeight'),
                              'fontSlant': char.get_style('fontSlant'),
                              'fontWidth': char.get_style('fontWidth'),
                              'fontSize': char.get_style('fontSize')}
                if current_style == 'box':
                    current_style = char_style
                elif char_style != current_style:
                    x_offset += self.typeset_span(pscanvas, current_style,
                                                  span_chars, span_char_widths)
                    span_chars = []
                    span_char_widths = []
                    current_style = char_style

                span_chars.append(char.glyph_name)
                span_char_widths.append(char_widths[i])

        if span_chars:
            self.typeset_span(pscanvas, current_style, span_chars,
                              span_char_widths)

        return max_font_size

    def typeset_span(self, canvas, style, span_chars, span_char_widths):
        """Typeset a series of characters with the same style"""
        font = style['typeface'].get(weight=style['fontWeight'],
                                     slant=style['fontSlant'],
                                     width=style['fontWidth'])
        font_wrapper = canvas.page.register_font(font.psFont, True)
        self.set_font(canvas, font_wrapper, style['fontSize'])
        span_char_widths_text = map(lambda f: "%.2f" % f, span_char_widths)
        ps_repr = font_wrapper.postscript_representation(span_chars)
        widths = " ".join(span_char_widths_text)
        print("({0}) [ {1} ] xshow".format(ps_repr, widths), file=canvas)
        return sum(span_char_widths)

    def typeset_box(self, pscanvas, x, y, box):
        box_canvas = canvas(pscanvas, x, y - box.depth, box.width,
                            box.height + box.depth)
        pscanvas.append(box_canvas)
        print(box.ps, file=box_canvas)
        # TODO: the following is probably not be the best way to do this
        print("( ) [ {} ] xshow".format(box.width), file=pscanvas)
        return box.width

    def set_font(self, pscanvas, wrapper, size):
        """Configure the output for a given font"""
        print("/{0} findfont".format(wrapper.ps_name()), file=pscanvas)
        print("{0} scalefont".format(float(size)), file=pscanvas)
        print("setfont", file=pscanvas)


class Paragraph(MixedStyledText, Flowable):
    style_class = ParagraphStyle

    def __init__(self, items, style=None):
        super().__init__(items, style=style)
        # TODO: move to TextStyle
        self.kerning = True
        self.ligatures = True
        #self.char_spacing = 0.0

        self._words = []
        self.wordpointer = 0
        self.first_line = True

    def _split_words(self):
        for is_space, item in itertools.groupby(self.characters(),
                                                lambda x: type(x) == Space):
            if is_space:
                for space in item:
                    self._words.append(space)
            else:
                self._words.append(Word(item, self.kerning, self.ligatures))

    def render(self, canvas, offset=0):
        return self.typeset(canvas, offset)

    # based on the typeset functions of psg.box.textbox
    def typeset(self, pscanvas, offset=0):
        if not self._words:
            self._split_words()

##        thisCanvas = pscanvas
##        print("gsave", file=thisCanvas)
##        thisCanvas.print_bounding_path()
##        print("[5 5] 0 setdash", file=thisCanvas)
##        print("stroke", file=thisCanvas)
##        print("grestore", file=thisCanvas)

        indent_left = float(self.get_style('indentLeft'))
        indent_right = float(self.get_style('indentRight'))
        indent_first = float(self.get_style('indentFirst'))
        line_width = pscanvas.w() - indent_left - indent_right

        self._line_cursor = pscanvas.h() - offset

        wordcount = 0
        indent = indent_left
        width = line_width
        if self.first_line:
            indent += indent_first
            width -= indent_first
        line = Line(self, width, indent)

        for i in range(self.wordpointer, len(self._words)):
            word = self._words[i]
            try:
                line.append(word)
            except EndOfLine as eol:
                try:
                    self.typeset_line(pscanvas, line)
                    wordcount = 0
                except EndOfBox:
                    self.wordpointer = i - wordcount
                    raise

                self.first_line = False

                line = Line(self, line_width, indent_left)
                if eol.hyphenation_remainder:
                    line.append(eol.hyphenation_remainder)
                else:
                    line.append(word)

            wordcount += 1

        # the last line
        if len(line) != 0:
            try:
                self.typeset_line(pscanvas, line, True)
            except EndOfBox:
                self.wordpointer = i - wordcount + 1
                raise

        return pscanvas.h() - offset - self._line_cursor

    def typeset_line(self, pscanvas, line, last_line=False):
        buffer = canvas(pscanvas, 0, 0, pscanvas.w(), pscanvas.h())
        line_height = line.typeset(buffer, last_line)
        try:
            self.newline(float(self.get_style('lineSpacing')) - line_height)
            buffer.write_to(pscanvas)
        except EndOfBox:
            #self._mark_line_cursor(pscanvas)
            raise
        finally:
            del buffer

    def _mark_line_cursor(self, pageCanvas):
        print("gsave", file=pageCanvas)
        print("newpath", file=pageCanvas)
        print("%f %f moveto" % (0, self._line_cursor), file=pageCanvas)
        print("%f %f lineto" % (10, self._line_cursor), file=pageCanvas)
        print("[5 5] 0 setdash", file=pageCanvas)
        print("stroke", file=pageCanvas)
        print("grestore", file=pageCanvas)

    def newline(self, line_height):
        """Move the cursor downwards by `line_height`"""
        self.advance(line_height)

    def advance(self, space):
        """Advance the line cursor downward by `space`. (No PostScript is
        generated by this function, it only updates an internal value!)

        """
        self._line_cursor -= space

        if self._line_cursor < 0:
            raise EndOfBox()
