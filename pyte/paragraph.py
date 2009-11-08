
#from pslib import PS_set_value, PS_set_parameter, PS_setfont, PS_show_boxed
#from pslib import *

from psg.drawing.box import textbox
from psg.util.measure import bounding_box
from psg.exceptions import *

from pyte.unit import pt
from pyte.font import FontStyle
from pyte.text import Text, TextStyle

class Justify:
    Left    = "left"
    Right   = "right"
    Center  = "center"
    Both    = "justify"


class ParagraphStyle(TextStyle):
    default = None

    # look at OpenOffice writer for more options
    def __init__(self, indentLeft=None, indentRight=None, indentFirst=None,
                 spaceAbove=None, spaceBelow=None,
                 lineSpacing=None,
                 justify=None,
                 typeface=None, fontStyle=None, fontSize=None, smallCaps=None,
                 hyphenate=None, hyphenChars=None, hyphenLang=None,
                 base=None):
        TextStyle.__init__(self, typeface, fontStyle, fontSize,
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

    # based on the typeset functions of psg.box.textbox
    def typeset(self, pscanvas):

##        thisCanvas = pscanvas
##        print("gsave", file=thisCanvas)
##        thisCanvas.print_bounding_path()
##        print("[5 5] 0 setdash", file=thisCanvas)
##        print("stroke", file=thisCanvas)
##        print("grestore", file=thisCanvas)

        line = []
        lineWidth = 0

##        pscanvas.print_bounding_path()
        self._line_cursor = pscanvas.h()

        for text in self.__text:
##            text.style.base = self.style
            typeface = text.style.typeface

            font = typeface.font(text.style.fontStyle)
            fontWrapper = pscanvas.page.register_font(font.psFont, True)
            spaceWidth = fontWrapper.font.metrics.stringwidth(
                " ", float(text.style.fontSize))

            for word in text.text.split():
                wordWidth = fontWrapper.font.metrics.stringwidth(
                    word, text.style.fontSize.evaluate(),
                    True, 0)

                if lineWidth + wordWidth > pscanvas.w():
                    lineHeight = self.typesetLine(pscanvas, pscanvas.w(), line)
                    self.newline(lineHeight)
                    line = []
                    lineWidth = 0
                else:
                    line.append( (Text(word, text.style), wordWidth,) )
                    lineWidth += wordWidth + spaceWidth

        if len(line) != 0:
            lineHeight = self.typesetLine(pscanvas, pscanvas.w(), line, True)
            self.newline(lineHeight)

        self.advance(self.style.lineSpacing.evaluate())

        return (- self._line_cursor, 0)

    def setFont(self, pscanvas, fontWrapper, fontSize=10):
        print("/{0} findfont".format(fontWrapper.ps_name()), file=pscanvas)
        print("{0} scalefont".format(fontSize.evaluate()), file=pscanvas)
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

        for (text, wordWidth) in words:
            word = text.text
            typeface = text.style.typeface
            font = typeface.font(text.style.fontStyle)
            fontWrapper = pscanvas.page.register_font(font.psFont, True)
            self.setFont(pscanvas, fontWrapper, text.style.fontSize)
            currentFontSize = float(text.style.fontSize)
            if currentFontSize > maxFontSize:
                maxFontSize = currentFontSize

            for idx in range(len(word)):
                char = ord(word[idx])

                if self.kerning:
                    try:
                        next = ord(word[idx+1])
                    except IndexError:
                        next = 0

                    kerning = fontWrapper.font.metrics.kerning_pairs.get(
                        ( char, next, ), 0.0)
                    kerning = kerning * currentFontSize / 1000.0
                else:
                    kerning = 0.0

                if idx == len(word) - 1:
                    spacing = 0.0
                else:
                    spacing = self.char_spacing

                char_width = fontWrapper.font.metrics.stringwidth(
                    chr(char), currentFontSize) + kerning + spacing

                chars.append(char)
                char_widths.append(char_width)

            # The space between...
            if words: # if it's not the last one...
                chars.append(32) # space
                char_widths.append(None)

        line_width = sum(filter(lambda a: a is not None, char_widths))

        if self.alignment in ("left", "center", "right",) or \
               (self.alignment == "justify" and lastLine):
            space_width = fontWrapper.font.metrics.stringwidth(
                " ", currentFontSize)
        else:
            space_width = (width - line_width) / float(word_count-1)


        n = []
        for a in char_widths:
            if a is None:
                n.append(space_width)
            else:
                n.append(a)
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

        char_widths = map(lambda f: "%.2f" % f, char_widths)
        tpl = ( fontWrapper.postscript_representation(chars),
                    " ".join(char_widths), )
        print("({0}) [ {1} ] xshow".format(tpl[0], tpl[1]), file=pscanvas)

        return maxFontSize

        #######################

        bb = bounding_box(left, bottom, left + width, bottom + height)
        psBox = textbox.from_bounding_box(pscanvas, bb, border=True)

        psBox.set_font(tr, font_size=11, paragraph_spacing=5.5,
                         alignment="justify", kerning=True)
        psBox.typeset()



        #psFont = font.loadFont(psdoc)
        #fontsize = float(self.style.fontSize)
        #PS_setfont(psdoc, psFont, fontsize)
        #PS_set_value(psdoc, "leading",        self.style.lineSpacing)
        #PS_set_value(psdoc, "parindent",      self.style.indentFirst)
        #PS_set_value(psdoc, "parskip",        self.style.spaceAbove + self.style.spaceBelow)
        #PS_set_value(psdoc, "numindentlines", 1)
        #PS_set_parameter(psdoc, "hyphenation", str(self.style.hyphenate).lower())
        #PS_set_parameter(psdoc, "hyphendict", "hyph_" + self.style.hyphenLang + ".dic")
        #PS_set_value(psdoc, "hyphenminchars", self.style.hyphenChars)
        #PS_rect(psdoc, left, bottom, width, height)
#        PS_glyph_show(psdoc, "A")
#        PS_glyph_show(psdoc, "a.sc")
#        for i in range (81,160):
#            print i, PS_symbol_name(psdoc, i, psFont)
#            PS_symbol(psdoc, i)
        #PS_stroke(psdoc)
        if rest == None:
            text = self.text
        else:
            text = self.text[-rest:]
        rest = PS_show_boxed(psdoc, text, left, bottom, width, height, self.style.justify, "")
        return rest

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
