
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

# margins
# ----------------------------------------------------------------------------
topmargin = bottommargin = 1.125*inch
leftmargin = rightmargin = 0.85*inch
column_spacing = 0.25*inch

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

# pages and their layout
# ----------------------------------------------------------------------------

class FirstPage(Page):
    def __init__(self, document):
        super().__init__(document.psg_doc, Letter, PORTRAIT)
        body = Container(self, leftmargin, topmargin,
                         self.width() - (leftmargin + rightmargin),
                         self.height() - (topmargin + bottommargin))

        self.title_box = Container(body, 0*pt, 0*pt)
        column_height = body.height() - self.title_box.height()
        column_top = self.title_box.bottom()
        column_width = (body.width() - column_spacing) / 2.0

        self.content = document.content

        column1 = Container(body, 0*pt, column_top,
            width=column_width, height=column_height, chain=document.content)
        column2 = Container(body, column_width + column_spacing, column_top,
            width=column_width, height=column_height, chain=document.content)

class OtherPage(Page):
    def __init__(self, document):
        super().__init__(document.psg_doc, Letter, PORTRAIT)
        body = Container(self, leftmargin, topmargin,
                         self.width() - (leftmargin + rightmargin),
                         self.height() - (topmargin + bottommargin))

        column_height = body.height()
        column_top = 0*pt
        column_width = (body.width() - column_spacing) / 2.0

        self.content = document.content

        column1 = Container(body, 0*pt, column_top,
            width=column_width, height=column_height, chain=document.content)
        column2 = Container(body, column_width + column_spacing, column_top,
            width=column_width, height=column_height, chain=document.content)


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
    def render(self, target):
        print('Section.render() %s' % self.attrib['title'])
        heading = Heading(1, self.attrib['title'])
        target.addParagraph(heading)
        for element in self.getchildren():
            element.render(target)


class P(CustomElement):
   def render(self, target):
        print('P.render()')
        content = self.text
        for child in self.getchildren():
            content += child.render(target)
            if child.tail is not None:
                content += child.tail
        paragraph = Paragraph(content)
        target.addParagraph(paragraph)


class B(CustomElement):
    def render(self, target):
        print('B.render()')
        return Bold(self.text)


class Em(CustomElement):
    def render(self, target):
        print('Em.render()')
        return Emphasis(self.text)


class SC(CustomElement):
    def render(self, target):
        print('SC.render()')
        return self.text.upper()


class OL(CustomElement):
    def render(self, target):
        print('OL.render()')
        items = self.getchildren()
        list = List()
        for item in items:
            list.append(item.render(target))
        target.addParagraph(list)


class LI(CustomElement):
    def render(self, target):
        print('LI.render()')
        content = self.text
        for child in self.getchildren():
            content += child.render(target)
            if child.tail is not None:
                content += child.tail
        return content


# main document
# ----------------------------------------------------------------------------

class RFIC2009Paper(Document):
    def __init__(self, filename):
        rngschema = 'rfic.rng'

        lookup = etree.ElementNamespaceClassLookup()
        namespace = lookup.get_namespace('http://www.mos6581.org/ns/rficpaper')
        namespace[None] = CustomElement
        namespace.update(dict([(cls.__name__.lower(), cls)
                               for cls in CustomElement.__subclasses__()]))

        Document.__init__(self, filename, 'template.xml', rngschema, lookup)


        authors = [author.text for author in self.root.head.authors.author]
        if len(authors) > 1:
            self.author = ', '.join(authors[:-1]) + ', and ' + authors[-1]
        else:
            self.author = authors[0]
        self.title = self.root.head.title.text
        self.keywords = [term.text for term in self.root.head.indexterms.term]

        self.content = Chain()

    def render(self):
        page = FirstPage(self)
        self.addPage(page)
        second_page = OtherPage(self)
        self.addPage(second_page)

        title = Paragraph(self.title, titleStyle)
        author = Paragraph(self.author, authorStyle)
        affiliation = Paragraph(self.root.head.affiliation.text, affiliationStyle)
        abstract = Abstract(self.root.head.abstract.text, abstractStyle)
        index_terms = IndexTerms(self.keywords, abstractStyle)

        page.title_box.addParagraph(title)
        page.title_box.addParagraph(author)
        page.title_box.addParagraph(affiliation)

        page.content.addParagraph(abstract)
        page.content.addParagraph(index_terms)

        for section in self.root.body.section:
            section.render(self.content)

        Document.render(self)
