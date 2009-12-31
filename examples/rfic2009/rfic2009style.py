
from copy import copy

from pyte import *
from pyte.unit import *
from pyte.font import *
from pyte.paper import  *
from pyte.document import *
from pyte.layout import *
from pyte.paragraph import *
from pyte.text import *
from pyte.structure import *

# margins
# ----------------------------------------------------------------------------
topmargin     = 1.125*inch
bottommargin  = topmargin
leftmargin    = 0.85*inch
rightmargin   = leftmargin
columnspacing = 0.25*inch

# fonts
# ----------------------------------------------------------------------------
termesRoman = Font("TeXGyreTermes-Regular", "qtmr")
termesBold = Font("TeXGyreTermes-Bold", "qtmb")
termesItalic = Font("TeXGyreTermes-Italic", "qtmri")
termesBoldItalic = Font("TeXGyreTermes-BoldItalic", "qtmbi")

termes = TypeFace("TeXGyreTermes",
                    roman=termesRoman, bold=termesBold,
                    italic=termesItalic, bolditalic=termesBoldItalic)

ieeeFamily = TypeFamily(serif=termes)

# page
# ----------------------------------------------------------------------------
page = Page(Letter)

# layout
# ----------------------------------------------------------------------------
body = Container(page,
                 leftmargin,
                 topmargin,
                 page.width() - (leftmargin + rightmargin),
                 page.height() - (topmargin + bottommargin))

titleBox = Container(body, 0*pt, 0*pt)

columnwidth = (body.width() - columnspacing) / 2.0
columnheight = body.height() - titleBox.height()

columns = Chain()
column1 = Container(body, 0*pt, titleBox.bottom(),
    width=columnwidth, height=columnheight, chain=columns)
column2 = Container(body, columnwidth + columnspacing, titleBox.bottom(),
    width=columnwidth, height=columnheight, chain=columns)

# custom paragraphs
# ----------------------------------------------------------------------------
class Abstract(Paragraph):
    def __init__(self, text, style):
        text = Text("Abstract &mdash; ", boldItalicStyle) + text
        Paragraph.__init__(self, text, style)

class IndexTerms(Paragraph):
    def __init__(self, terms, style):
        terms = copy(terms)
        terms.sort()
        terms[0] = terms[0][0].upper() + terms[0][1:]
        text = Text("Index Terms &mdash; ", boldItalicStyle) + ", ".join(terms) + "."
        Paragraph.__init__(self, text, style)

# paragraph styles
# ----------------------------------------------------------------------------

titleStyle = ParagraphStyle("title",
                            typeface=ieeeFamily.serif,
                            fontStyle=FontStyle.Roman,
                            fontSize=18*pt,
                            lineSpacing=1.2*18*pt,
                            indentLeft=nil,
                            indentRight=nil,
                            indentFirst=nil,
                            spaceAbove=6*pt,
                            spaceBelow=6*pt,
                            justify=Justify.Center)
authorStyle = ParagraphStyle("author",
                             base=titleStyle,
                             fontSize=12*pt,
                             lineSpacing=1.2*12*pt)
affiliationStyle = ParagraphStyle("affiliation",
                                  base=authorStyle,
                                  spaceBelow=6*pt + 12*pt)
abstractStyle = ParagraphStyle("abstract",
                               typeface=ieeeFamily.serif,
                               fontStyle=FontStyle.Bold,
                               fontSize=9*pt,
                               lineSpacing=10*pt,
                               indentFirst=0.125*inch,
                               spaceAbove=0*pt,
                               spaceBelow=0*pt,
                               justify=Justify.Both)

bodyStyle = ParagraphStyle("body",
                           typeface=ieeeFamily.serif,
                           fontStyle=FontStyle.Roman,
                           fontSize=10*pt,
                           lineSpacing=12*pt,
                           indentLeft=0*pt,
                           indentRight=0*pt,
                           indentFirst=0.125*inch,
                           spaceAbove=0*pt,
                           spaceBelow=0*pt,
                           justify=Justify.Both)
listStyle = ListStyle("list",
                      base=bodyStyle,
                      spaceAbove=5*pt,
                      spaceBelow=5*pt,
                      ordered=False,
                      itemSpacing=bodyStyle.lineSpacing)


hd1Style = HeadingStyle("heading",
                       typeface=ieeeFamily.serif,
                       fontStyle=FontStyle.Roman,
                       fontSize=10*pt,
                       smallCaps=True,
                       justify=Justify.Center,
                       lineSpacing=12*pt,
                       indentFirst=nil,
                       spaceAbove=18*pt,
                       spaceBelow=6*pt,
                       numberingStyle=NumberingStyle.Roman)

hd2Style = HeadingStyle("subheading",
                       typeface=ieeeFamily.serif,
                       fontStyle=FontStyle.Italic,
                       fontSize=10*pt,
                       smallCaps=False,
                       justify=Justify.Left,
                       lineSpacing=12*pt,
                       indentFirst=nil,
                       spaceAbove=6*pt,
                       spaceBelow=6*pt,
                       numberingStyle=NumberingStyle.Character)
#TODO: should only specify style once for each level!


HeadingStyle.default = []
HeadingStyle.default.append(hd1Style)
HeadingStyle.default.append(hd2Style)

ParagraphStyle.default = bodyStyle
TextStyle.default = TextStyle("RFIC2009 default",
                           typeface=ieeeFamily.serif,
						   fontStyle=FontStyle.Roman,
						   fontSize=6*pt)
ListStyle.default = listStyle


class RFIC2009Paper(Document):
    def __init__(self, filename):
        Document.__init__(self, filename)
        self.title = "<title>"
        self.author = "<author>"
        self.affiliation = "<affiliation>"
        self.abstract = "<abstract>"
        self.indexTerms = ["index", "terms"]
        #self.addMasterPage(page) # TODO: implement "master pages"
        self.content = columns
        self.addPage(page)

    def render(self):
        self.keywords = self.indexTerms
        # paragraphs - TODO: clean up
        # ----------------------------------------------------------------------
        parTitle = Paragraph(self.title, titleStyle)
        parAuthor = Paragraph(self.author, authorStyle)
        parAffiliation = Paragraph(self.affiliation, affiliationStyle)
        parAbstract = Abstract(self.abstract, abstractStyle)
        parIndexTerms = IndexTerms(self.indexTerms, abstractStyle)

        titleBox.addParagraph(parTitle)
        titleBox.addParagraph(parAuthor)
        titleBox.addParagraph(parAffiliation)

        columns._TextTarget__paragraphs.insert(0, parAbstract)
        columns._TextTarget__paragraphs.insert(1, parIndexTerms)

        Document.render(self)
