
from psg.drawing.box import canvas
from psg.util.measure import bounding_box
from psg.exceptions import *

from pyte.unit import pt
from pyte.font import FontStyle
from pyte.text import StyledText, Word, Character, Space, TextStyle, ParentStyle, MixedStyledText, Glyph


class Justify:
    Left = "left"
    Right = "right"
    Center = "center"
    Both = "justify"


# TODO: look at Word/OpenOffice for more options
class ParagraphStyle(TextStyle):
    attributes = {'indentLeft': 0*pt,
                  'indentRight': 0*pt,
                  'indentFirst': 0*pt,
                  'spaceAbove': 0*pt,
                  'spaceBelow': 0*pt,
                  'lineSpacing': 10*pt, # TODO: change default
                  'justify': Justify.Both}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


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
        if isinstance(item, Word):
            args = (self.paragraph.kerning, )
            if self.paragraph.ligatures:
                item = item.substitute_ligatures()
        else:
            args = ()
        assert isinstance(item, Word) or isinstance(item, Space)
        width = item.width(*args)
        if isinstance(item, Word) and self.text_width + width > self.width:
            for first, second in item.hyphenate():
                first_width = first.width(*args)
                if self.text_width + first_width < self.width:
                    self.text_width += first_width
                    super().append(first)
                    raise EndOfLine(second)
            raise EndOfLine
        self.text_width += width
        super().append(item)

    def typeset(self, pscanvas, last_line=False):
        """Typeset words on the current coordinates"""
        chars = []
        char_widths = []
        max_font_size = 0
        justification = self.paragraph.get_style('justify')
        kerning = self.paragraph.kerning

        # calculate total width of all characters (excluding spaces)
        for word in self:
            if isinstance(word, Space):
                if word is not self[-1]:
                    chars.append(word)
                    char_widths.append(0.0)
                    # TODO: handle Spacer
                    #char_widths.append(word.width())
            else:
                for j, character in enumerate(word):
                    current_font_size = float(character.get_style('fontSize'))
                    max_font_size = max(current_font_size, max_font_size)
                    kerning = word.kerning(j) if kerning else 0.0

                    chars.append(character)
                    char_widths.append(character.width() + kerning) #+ spacing

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
                    char_widths[i] = char.width()
                    line_width += char.width()
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

        current_style = {'typeface': chars[0].get_style('typeface'),
                         'fontStyle': chars[0].get_style('fontStyle'),
                         'fontSize': chars[0].get_style('fontSize')}
        span_chars = []
        span_char_widths = []
        for i, char in enumerate(chars):
            char_style = {'typeface': char.get_style('typeface'),
                          'fontStyle': char.get_style('fontStyle'),
                          'fontSize': char.get_style('fontSize')}
            if char_style != current_style:
                self.typeset_span(pscanvas, current_style, span_chars,
                                  span_char_widths)
                span_chars = []
                span_char_widths = []
                current_style = char_style

            span_chars.append(char.ord())
            span_char_widths.append(char_widths[i])

        self.typeset_span(pscanvas, current_style, span_chars, span_char_widths)

        return max_font_size

    def typeset_span(self, canvas, style, span_chars, span_char_widths):
        """Typeset a series of characters with the same style"""
        font = style['typeface'].font(style['fontStyle'])
        font_wrapper = canvas.page.register_font(font.psFont, True)
        self.set_font(canvas, font_wrapper, style['fontSize'])
        span_char_widths = map(lambda f: "%.2f" % f, span_char_widths)
        ps_repr = font_wrapper.postscript_representation(span_chars)
        widths = " ".join(span_char_widths)
        print("({0}) [ {1} ] xshow".format(ps_repr, widths), file=canvas)

    def set_font(self, pscanvas, wrapper, size):
        """Configure the output for a given font"""
        print("/{0} findfont".format(wrapper.ps_name()), file=pscanvas)
        print("{0} scalefont".format(float(size)), file=pscanvas)
        print("setfont", file=pscanvas)


class Paragraph(MixedStyledText):
    style_class = ParagraphStyle

    def __init__(self, items, style=None):
        super().__init__(items, style=style)
        # TODO: move to ParagraphStyle
        self.kerning = True
        self.ligatures = True
        #self.char_spacing = 0.0

        self._split_words()
        self.wordpointer = 0
        self.first_line = True

    def _split_words(self):
        self._words = []
        word = Word()
        for char in self.characters():
            if isinstance(char, Space):
                self._words.append(word)
                self._words.append(char)
                word = Word()
            else:
                word.append(char)

        if len(word) > 0:
            self._words.append(word)

    # based on the typeset functions of psg.box.textbox
    def typeset(self, pscanvas, offset=0):
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
                self.wordpointer = i - wordcount
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
