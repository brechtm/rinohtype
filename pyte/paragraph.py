
from psg.drawing.box import canvas
from psg.util.measure import bounding_box
from psg.exceptions import *

from pyte.unit import pt
from pyte.font import FontStyle
from pyte.text import StyledText, Word, Character, Space, TextStyle, ParentStyle, MixedStyledText


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


class Line(list):
    def __init__(self):
        super().__init__()

    def append(self, item):
        assert isinstance(item, Word) or isinstance(item, Space)
        super().append(item)

    def typeset(self, pscanvas, justification):
        # TODO: implement Line.typeset()
        pass


class Paragraph(MixedStyledText):
    style_class = ParagraphStyle

    def __new__(cls, items, style=None):
        obj = super().__new__(cls, items, style=style)
        return obj

    def __init__(self, items, style=None):
        super().__init__(items, style=style)
        # TODO: move to ParagraphStyle
        self.kerning = True
        #self.char_spacing = 0.0

        self._split_words()
        self.wordpointer = 0
        self.firstLine = True

    def _split_words(self):
        self.__words = []
        word = Word()
        for char in self.characters():
            if isinstance(char, Space):
                self.__words.append(word)
                self.__words.append(char)
                word = Word()
            else:
                word.append(char)

        if len(word) > 0:
            self.__words.append(word)

    # based on the typeset functions of psg.box.textbox
    def typeset(self, pscanvas, offset=0):
##        thisCanvas = pscanvas
##        print("gsave", file=thisCanvas)
##        thisCanvas.print_bounding_path()
##        print("[5 5] 0 setdash", file=thisCanvas)
##        print("stroke", file=thisCanvas)
##        print("grestore", file=thisCanvas)

        line = Line()
        lineWidth = 0
        lineHeight = 0

        #print(self)

        indent_left = float(self.get_style('indentLeft'))
        indent_right = float(self.get_style('indentRight'))
        indent_first = float(self.get_style('indentFirst'))
        available_width = pscanvas.w() - indent_left - indent_right

##        pscanvas.print_bounding_path()
        self._line_cursor = pscanvas.h() - offset

        wordcount = 0

        #for word in self.__words:
        numwords = len(self.__words)
        for i in range(self.wordpointer, numwords):
            word = self.__words[i]
            wordWidth = word.width()

            if self.firstLine:
                indent = indent_left + indent_first
                width = available_width - indent_first
            else:
                indent = indent_left
                width = available_width

            if (isinstance(word, Word) and
                    lineWidth + wordWidth > available_width):
                buffer = canvas(pscanvas, 0, 0, pscanvas.w(), pscanvas.h())
                lineHeight = self.typesetLine(buffer, width, line, indent)
                # line spacing
                try:
                    self.newline(float(self.get_style('lineSpacing') - lineHeight*pt))
                    buffer.write_to(pscanvas)
                    wordcount = 0
                except EndOfBox:
                    self._mark_line_cursor(pscanvas)
                    self.wordpointer = i - wordcount
                    raise
                finally:
                    del buffer
                if self.firstLine:
                    self.firstLine = False
                line = Line()
                lineWidth = 0

            line.append(word)
            lineWidth += wordWidth
            wordcount += 1

        if len(line) != 0:
            a = len(line[0])
            buffer = canvas(pscanvas, 0, 0, pscanvas.w(), pscanvas.h())
            lineHeight = self.typesetLine(buffer, width, line, indent, True)
            try:
                self.newline(float(self.get_style('lineSpacing') - lineHeight*pt))
                buffer.write_to(pscanvas)
                wordcount = 0
            except EndOfBox:
                self._mark_line_cursor(pscanvas)
                self.wordpointer = i - wordcount
                raise
            finally:
                del buffer

        return pscanvas.h() - self._line_cursor - offset

    def _mark_line_cursor(self, pageCanvas):
        print("gsave", file=pageCanvas)
        print("newpath", file=pageCanvas)
        print("%f %f moveto" % (0, self._line_cursor), file=pageCanvas)
        print("%f %f lineto" % (10, self._line_cursor), file=pageCanvas)
        print("[5 5] 0 setdash", file=pageCanvas)
        print("stroke", file=pageCanvas)
        print("grestore", file=pageCanvas)

    def setFont(self, pscanvas, fontWrapper, fontSize):
        print("/{0} findfont".format(fontWrapper.ps_name()), file=pscanvas)
        print("{0} scalefont".format(float(fontSize)), file=pscanvas)
        print("setfont", file=pscanvas)

        ## Cursor
        #try:
        #    if self.font_wrapper is not None: self.newline()
        #except EndOfBox:
        #    raise BoxTooSmall("The box is smaller than the line height.")


    def typesetLine(self, pscanvas, width, words, indent=0, lastLine=False):
        """
        Typeset words on the current coordinates.
        """
        chars = []
        char_widths = []
        maxFontSize = 0

        for word in words:
            if isinstance(word, Space):
                if word is not words[-1]:
                    # TODO: handle Spacer
                    chars.append(word)
                    char_widths.append(0.0)
                    #char_widths.append(word.width())
            else:
                for j in range(len(word)):
                    character = word[j]
                    currentFontSize = float(character.get_style('fontSize'))
                    #print('%s (%g)' % (character.text, currentFontSize))
                    if currentFontSize > maxFontSize:
                        maxFontSize = currentFontSize
                    char_or_glyph = character.ord()

                    if self.kerning and j < len(word) - 1:
                        kerning = word.kerning(j)
                    else:
                        kerning = 0.0

                    chars.append(character)
                    char_widths.append(character.width() + kerning) #+ spacing

        line_width = sum(char_widths)

        if self.get_style('justify') == "justify" and not lastLine:
            try:
                number_of_words = list(map(type, words)).count(Word)
                space_width = (width - line_width) / (number_of_words - 1)
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
            extra_space = width - line_width

        # Horizontal displacement
        if self.get_style('justify') in ("left", "justify",):
            x = 0.0
        elif self.get_style('justify') == "center":
            x = extra_space / 2.0
        elif self.get_style('justify') == "right":
            x = extra_space

        self._line_cursor -= maxFontSize

        # Position PostScript's cursor
        print("{0} {1} moveto".format(x, self._line_cursor), file=pscanvas)

        # indenting
        if indent != 0:
            print("{} 0 rmoveto".format(indent), file=pscanvas)

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
                typeface = char.get_style('typeface')
                font = typeface.font(current_style['fontStyle'])
                fontWrapper = pscanvas.page.register_font(font.psFont, True)
                self.setFont(pscanvas, fontWrapper, current_style['fontSize'])
                span_char_widths = map(lambda f: "%.2f" % f, span_char_widths)
                tpl = (fontWrapper.postscript_representation(span_chars),
                       " ".join(span_char_widths))
                print("({0}) [ {1} ] xshow".format(tpl[0], tpl[1]), file=pscanvas)
                span_chars = []
                span_char_widths = []
                current_style = char_style

            span_chars.append(char.ord())
            span_char_widths.append(char_widths[i])

        typeface = current_style['typeface']
        font = typeface.font(current_style['fontStyle'])
        fontWrapper = pscanvas.page.register_font(font.psFont, True)
        self.setFont(pscanvas, fontWrapper, current_style['fontSize'])
        span_char_widths = map(lambda f: "%.2f" % f, span_char_widths)
        tpl = (fontWrapper.postscript_representation(span_chars),
               " ".join(span_char_widths))
        print("({0}) [ {1} ] xshow".format(tpl[0], tpl[1]), file=pscanvas)

        return maxFontSize

    def newline(self, lineHeight):
        """Move the cursor downwards one line. In debug mode (psg.debug.debug
        is set to verbose) this function will draw a thin gray line below every
        line. (No PostScript is generated by this function!)

        """
        self.advance(lineHeight)

    def advance(self, space):
        """Advance the line cursor downward by space. (No PostScript is
        generated by this function, it only updates an internal value!)

        """
        self._line_cursor -= space

        if self._line_cursor < 0:
            raise EndOfBox()

    def text_height(self):
        if self._line_cursor < 0:
            l = 0
        else:
            l = self._line_cursor

        return self.h() - l
