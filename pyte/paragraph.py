
#from pslib import PS_set_value, PS_set_parameter, PS_setfont, PS_show_boxed
#from pslib import *

from psg.drawing.box import textbox
from psg.util.measure import bounding_box
from psg.exceptions import *

from pyte.unit import pt
from pyte.font import FontStyle
from pyte.text import Text, Word, Character, Space, TextStyle

class Justify:
    Left    = "left"
    Right   = "right"
    Center  = "center"
    Both    = "justify"


class ParagraphStyle(TextStyle):
    default = None

    # look at OpenOffice writer for more options
    def __init__(self, name="", indentLeft=None, indentRight=None, indentFirst=None,
                 spaceAbove=None, spaceBelow=None,
                 lineSpacing=None,
                 justify=None,
                 typeface=None, fontStyle=None, fontSize=None, smallCaps=None,
                 hyphenate=None, hyphenChars=None, hyphenLang=None,
                 base=None):
        TextStyle.__init__(self, name, typeface, fontStyle, fontSize,
                smallCaps,
                hyphenate, hyphenChars, hyphenLang)
        if indentLeft is not None: self.indentLeft = indentLeft
        if indentRight is not None: self.indentRight = indentRight
        if indentFirst is not None: self.indentFirst = indentFirst
        if spaceAbove is not None: self.spaceAbove = spaceAbove
        if spaceBelow is not None: self.spaceBelow = spaceBelow
        # TODO: http://lists.planix.com/pipermail/lout-users/2006q2/004181.html
        if lineSpacing is not None: self.lineSpacing = lineSpacing
        if justify is not None: self.justify = justify
        if base:
            assert isinstance(base, ParagraphStyle)
            self.base = base
        else:
            self.base = ParagraphStyle.default

##        if self.base is None:
##            assert(indentLeft is not None)
##            assert(indentRight is not None)
##            assert(indentFirst is not None)
##            assert(spaceAbove is not None)
##            assert(spaceBelow is not None)
##            assert(lineSpacing is not None)
##            assert(justify is not None)
##            assert(typeface is not None)
##            assert(fontStyle is not None)
##            assert(fontSize is not None)
##            assert(smallCaps is not None)
##            assert(hyphenate is not None)
##            assert(hyphenChars is not None)
##            assert(hyphenLang is not None)

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.base.__getattribute__(name)

##ParagraphStyle.default = ParagraphStyle(indentLeft = 0*pt,
##                                        indentRight = 0*pt,
##                                        indentFirst = 0*pt,
##                                        spaceAbove = 0*pt,
##                                        spaceBelow = 0*pt,
##                                        lineSpacing = 10*pt,    # TODO: change default
##                                        justify = Justify.Both,
##                                        typeface = None,
##                                        fontStyle = FontStyle.Roman,
##                                        fontSize = 10*pt, # TODO: change default
##                                        smallCaps = False,
##                                        hyphenate = True,
##                                        hyphenChars = 2,
##                                        hyphenLang = "en")


class Line(list):
    def __init__(self):
        list.__init__(self)

    def append(self, item):
        assert isinstance(item, Word) or isinstance(item, Space)
        list.append(self, item)

    def typeset(self, pscanvas, justification):
        # TOOD: implement Line.typeset()
        pass


class DefaultStyle:
    pass

class Paragraph(object):
    def __init__(self, style=DefaultStyle):
        self.__text = []
        if style == DefaultStyle:
            self.style = ParagraphStyle.default
        else:
            self.style = style

        self.kerning = True # self.style.kerning
        self.char_spacing = 0.0
        self.alignment = self.style.justify

    def __lshift__(self, item):
        if type(item) == str:
            item = Text(item, style=self.style)
        self.__text.append(item)
        return self

    def __splitWords(self):
        self.__words = []
        word = Word()
        for text in self.__text:
            for character in text.text:
                if character not in (" ", "\t"):
                    word.append(Character(character, style=text.style))
                else:
                    self.__words.append(word)
                    self.__words.append(Space(style=text.style))
                    word = Word()

        if len(word) > 0:
            self.__words.append(word)

    # based on the typeset functions of psg.box.textbox
    def typeset(self, pscanvas, offset=0):

        # TODO: preprocess text for ', ", --, ---, and other markup shortcuts
        self.__splitWords()

##        thisCanvas = pscanvas
##        print("gsave", file=thisCanvas)
##        thisCanvas.print_bounding_path()
##        print("[5 5] 0 setdash", file=thisCanvas)
##        print("stroke", file=thisCanvas)
##        print("grestore", file=thisCanvas)

        line = Line()
        lineWidth = 0
        lineHeight = 0

##        pscanvas.print_bounding_path()
        self._line_cursor = pscanvas.h() - offset

        for word in self.__words:
            wordWidth = word.width()

            if isinstance(word, Word):
                if lineWidth + wordWidth > pscanvas.w():
                    lineHeight = self.typesetLine(pscanvas, pscanvas.w(), line)
                    #self.newline(lineHeight)
                    line = Line()
                    lineWidth = 0

                line.append(word)

            lineWidth += wordWidth

        if len(line) != 0:
            a = len(line[0])
            lineHeight = self.typesetLine(pscanvas, pscanvas.w(), line, True)
##            self.newline(lineHeight)

##        self.advance(float(self.style.lineSpacing - lineHeight*pt))

        return pscanvas.h() - self._line_cursor - offset

    def setFont(self, pscanvas, fontWrapper, fontSize):
        print("/{0} findfont".format(fontWrapper.ps_name()), file=pscanvas)
        print("{0} scalefont".format(float(fontSize)), file=pscanvas)
        print("setfont", file=pscanvas)

        ## Cursor
        #try:
        #    if self.font_wrapper is not None: self.newline()
        #except EndOfBox:
        #    raise BoxTooSmall("The box is smaller than the line height.")


    def typesetLine(self, pscanvas, width, words, lastLine=False):
        """
        Typeset words on the current coordinates. Words is a list of pairs
        as ( 'word', width, ).
        """
        chars = []
        char_widths = []
        maxFontSize = 0

        word_count = len(words)

        for i, word in enumerate(words):

            for j in range(len(word)):
                character = word[j]
                currentFontSize = float(character.style.fontSize)
                if currentFontSize > maxFontSize:
                    maxFontSize = currentFontSize
                char = character.ord()

                if self.kerning and j < len(word) - 1:
                    kerning = word.kerning(j)
                else:
                    kerning = 0.0

##                if idx == len(word) - 1:
##                    spacing = 0.0
##                else:
##                    spacing = self.char_spacing

                char_width = character.width() + kerning #+ spacing

                chars.append(character)
                char_widths.append(char_width)

            # The space between...
            if i < len(words) - 1: # if it's not the last one...
                chars.append(Space(style=word[-1].style)) # space
                char_widths.append(None)

        line_width = sum(filter(lambda a: a is not None, char_widths))

        n = []
        if self.alignment == "justify" and not lastLine:
            space_width = (width - line_width) / float(word_count-1)
            for i, w in enumerate(char_widths):
                if w is None:
                    n.append(space_width)
                else:
                    n.append(w)
        else:
            for i, w in enumerate(char_widths):
                if w is None:
                    n.append(chars[i].width())
                else:
                    n.append(w)
        char_widths = n

        # Horizontal displacement
        if self.alignment in ("left", "justify",):
            x = 0.0
        elif self.alignment == "center":
            line_width = sum(char_widths)
            x = (width - line_width) / 2.0
        elif self.alignment == "right":
            line_width = sum(char_widths)
            x = width - line_width

        self._line_cursor -= maxFontSize

        # Position PostScript's cursor
        print("{0} {1} moveto".format(x, self._line_cursor), file=pscanvas)

        currentStyle = chars[0].style
        span_chars = []
        span_char_widths = []
        for i, char in enumerate(chars):
            if char.style != currentStyle:
                typeface = char.style.typeface
                font = typeface.font(currentStyle.fontStyle)
                fontWrapper = pscanvas.page.register_font(font.psFont, True)
                self.setFont(pscanvas, fontWrapper, currentStyle.fontSize)
                span_char_widths = map(lambda f: "%.2f" % f, span_char_widths)
                tpl = ( fontWrapper.postscript_representation(span_chars),
                            " ".join(span_char_widths), )
                print("({0}) [ {1} ] xshow".format(tpl[0], tpl[1]), file=pscanvas)
                span_chars = []
                span_char_widths = []
                currentStyle = char.style

            span_chars.append(char.ord())
            span_char_widths.append(char_widths[i])

        typeface = char.style.typeface
        font = typeface.font(currentStyle.fontStyle)
        fontWrapper = pscanvas.page.register_font(font.psFont, True)
        self.setFont(pscanvas, fontWrapper, currentStyle.fontSize)
        span_char_widths = map(lambda f: "%.2f" % f, span_char_widths)
        tpl = ( fontWrapper.postscript_representation(span_chars),
                    " ".join(span_char_widths), )
        print("({0}) [ {1} ] xshow".format(tpl[0], tpl[1]), file=pscanvas)


        return maxFontSize


    def newline(self, lineHeight):
        """
        Move the cursor downwards one line. In debug mode (psg.debug.debug
        is set to verbose) this function will draw a thin gray line below
        every line. (No PostScript is generated by this function!)
        """
        self.advance(lineHeight)

    def advance(self, space):
        """
        Advance the line cursor downward by space. (No PostScript is
        generated by this function, it only updates an internal
        value!)
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
