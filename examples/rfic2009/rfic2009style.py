
from copy import copy

from lxml import etree, objectify

from pyte import *
from pyte.unit import *
from pyte.font import *
from pyte.paper import Paper, Letter
from pyte.document import Document, Page, PORTRAIT
from pyte.layout import *
from pyte.paragraph import *
from pyte.text import *
from pyte.text import Em as Emphasis
from pyte.structure import *


# fonts
# ----------------------------------------------------------------------------
termes_roman = Font("qtmr")
termes_bold = Font("qtmb")
termes_italic = Font("qtmri")
termes_bold_italic = Font("qtmbi")

termes = TypeFace("TeXGyreTermes",
                  roman=termes_roman, bold=termes_bold,
                  italic=termes_italic, bolditalic=termes_bold_italic)

ieeeFamily = TypeFamily(serif=termes)


# paragraph styles
# ----------------------------------------------------------------------------
bodyStyle = ParagraphStyle('body',
                           typeface=ieeeFamily.serif,
                           fontStyle=FontStyle.Roman,
                           fontSize=10*pt,
                           lineSpacing=12*pt,
                           indentFirst=0.125*inch,
                           spaceAbove=0*pt,
                           spaceBelow=0*pt,
                           justify=Justify.Both)

ParagraphStyle.attributes['typeface'] = bodyStyle.typeface
ParagraphStyle.attributes['hyphenLang'] = 'en_US'
ParagraphStyle.attributes['hyphenChars'] = 4

titleStyle = ParagraphStyle("title",
                            typeface=ieeeFamily.serif,
                            fontStyle=FontStyle.Roman,
                            fontSize=18*pt,
                            lineSpacing=1.2*18*pt,
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

listStyle = ListStyle("list", base=bodyStyle,
                      spaceAbove=5*pt,
                      spaceBelow=5*pt,
                      indentLeft=0*inch,
                      indentFirst=0*inch,
                      ordered=True,
                      itemSpacing=bodyStyle.lineSpacing,
                      numberingStyle=NumberingStyle.Roman, # not yet implemented
                      numberingSeparator=')')

hd1Style = HeadingStyle("heading",
                        typeface=ieeeFamily.serif,
                        fontStyle=FontStyle.Roman,
                        fontSize=10*pt,
                        smallCaps=True,
                        justify=Justify.Center,
                        lineSpacing=12*pt,
                        spaceAbove=18*pt,
                        spaceBelow=6*pt,
                        numberingStyle=NumberingStyle.Roman)

acknowledgement_heading_style = HeadingStyle("acknowledgement", base=hd1Style,
                                             numberingStyle=None)

hd2Style = HeadingStyle("subheading", base=hd1Style,
                        fontStyle=FontStyle.Italic,
                        fontSize=10*pt,
                        smallCaps=False,
                        justify=Justify.Left,
                        lineSpacing=12*pt,
                        spaceAbove=6*pt,
                        spaceBelow=6*pt,
                        numberingStyle=NumberingStyle.Character)
#TODO: should only specify style once for each level!

heading_styles = [hd1Style, hd2Style]

# custom paragraphs
# ----------------------------------------------------------------------------
# FIXME: tricky to get right
##class Abstract(Paragraph):
##    def __new__(cls, text):
##        text = Text("Abstract &mdash; ", boldItalicStyle) + text
##        return super().__new__(cls, text, abstractStyle)


##class IndexTerms(Paragraph):
##    def __new__(cls, terms):
##        terms = copy(terms)
##        terms.sort()
##        terms[0] = terms[0][0].upper() + terms[0][1:]
##        text = Text("Index Terms &mdash; ", boldItalicStyle) + ", ".join(terms) + "."
##        return Paragraph.__new__(cls, text, abstractStyle)

def Abstract(text):
    text = StyledText("Abstract &mdash; ", boldItalicStyle) + text
    return Paragraph(text, style=abstractStyle)


def IndexTerms(terms):
    terms = sorted(terms)
    terms[0] = terms[0][0].upper() + terms[0][1:]
    text = StyledText("Index Terms &mdash; ", boldItalicStyle) + ", ".join(terms) + "."
    return Paragraph(text, style=abstractStyle)


# render methods
# ----------------------------------------------------------------------------

# ElementBase restrictions!!
# http://codespeak.net/lxml/element_classes.html

# is it a good idea to inherit from ObjectifiedElement (not documented)?
class CustomElement(objectify.ObjectifiedElement):
#class CustomElement(etree.ElementBase):
    def render(self, target):
        raise NotImplementedError('tag: %s' % self.tag)


class Section(CustomElement):
    def render(self, target, level=1):
        #print('Section.render() %s' % self.attrib['title'])
        heading = Heading(self.attrib['title'], style=heading_styles[level - 1],
                          level=level)
        target.addParagraph(heading)
        for element in self.getchildren():
            if type(element) == Section:
                element.render(target, level=level + 1)
            else:
                element.render(target)


class P(CustomElement):
   def render(self, target):
        #print('P.render()')
        content = self.text
        for child in self.getchildren():
            content += child.render(target)
            if child.tail is not None:
                content += child.tail
        paragraph = Paragraph(content, style=bodyStyle)
        target.addParagraph(paragraph)


class B(CustomElement):
    def render(self, target):
        #print('B.render()')
        return Bold(self.text)


class Em(CustomElement):
    def render(self, target):
        #print('Em.render()')
        return Emphasis(self.text)


class SC(CustomElement):
    def render(self, target):
        #print('SC.render()')
        return SmallCaps(self.text)


class OL(CustomElement):
    def render(self, target):
        #print('OL.render()')
        items = []
        for item in self.getchildren():
            items.append(item.render(target))
        lst = List(items, style=listStyle)
        target.addParagraph(lst)


class LI(CustomElement):
    def render(self, target):
        #print('LI.render()')
        content = self.text
        for child in self.getchildren():
            content += child.render(target)
            if child.tail is not None:
                content += child.tail
        return content

class Acknowledgement(CustomElement):
    def render(self, target):
        #print('Acknowledgement.render()')
        heading = Heading('Acknowledgement',
                          style=acknowledgement_heading_style, level=1)
        target.addParagraph(heading)
        for element in self.getchildren():
            element.render(target)


# pages and their layout
# ----------------------------------------------------------------------------
class RFICPage(Page):
    topmargin = bottommargin = 1.125*inch
    leftmargin = rightmargin = 0.85*inch
    column_spacing = 0.25*inch

    def __init__(self, document, first=False):
        super().__init__(document, Letter, PORTRAIT)
        body = Container(self, self.leftmargin, self.topmargin,
                         self.width() - (self.leftmargin + self.rightmargin),
                         self.height() - (self.topmargin + self.bottommargin))

        column_height = body.height()
        column_width = (body.width() - self.column_spacing) / 2.0
        column_top = 0*pt

        if first:
            self.title_box = Container(body, 0*pt, 0*pt)
            column_height -= self.title_box.height()
            column_top = self.title_box.bottom()

        self.content = document.content

        self.column1 = Container(body, 0*pt, column_top,
                                 width=column_width, height=column_height,
                                 chain=document.content)
        self.column2 = Container(body, column_width + self.column_spacing, column_top,
                                 width=column_width, height=column_height,
                                 chain=document.content)


# main document
# ----------------------------------------------------------------------------

class RFIC2009Paper(Document):
    rngschema = 'rfic.rng'

    def __init__(self, filename):
        lookup = etree.ElementNamespaceClassLookup()
        namespace = lookup.get_namespace('http://www.mos6581.org/ns/rficpaper')
        namespace[None] = CustomElement
        namespace.update(dict([(cls.__name__.lower(), cls)
                               for cls in CustomElement.__subclasses__()]))

        Document.__init__(self, filename, 'template.xml', self.rngschema,
                          lookup)

        authors = [author.text for author in self.root.head.authors.author]
        if len(authors) > 1:
            self.author = ', '.join(authors[:-1]) + ', and ' + authors[-1]
        else:
            self.author = authors[0]
        self.title = self.root.head.title.text
        self.keywords = [term.text for term in self.root.head.indexterms.term]

        self.content = Chain(self)

    def render(self):
        page = RFICPage(self, first=True)
        self.addPage(page)

        title = Paragraph(self.title, titleStyle)
        author = Paragraph(self.author, authorStyle)
        affiliation = Paragraph(self.root.head.affiliation.text,
                                affiliationStyle)
        abstract = Abstract(self.root.head.abstract.text)
        index_terms = IndexTerms(self.keywords)

        page.title_box.addParagraph(title)
        page.title_box.addParagraph(author)
        page.title_box.addParagraph(affiliation)

        page.content.addParagraph(abstract)
        page.content.addParagraph(index_terms)

        for section in self.root.body.section:
            section.render(self.content)

        try:
            self.root.body.acknowledgement.render(self.content)
        except AttributeError:
            pass

        Document.render(self)

    def add_to_chain(self, chain):
        page = RFICPage(self)
        self.addPage(page)
        return page.column1
