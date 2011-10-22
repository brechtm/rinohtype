
from copy import copy

from lxml import etree, objectify

from pyte.unit import inch, pt
from pyte.font import Font, TypeFace, TypeFamily, FontStyle
from pyte.paper import Paper, Letter
from pyte.document import Document, Page, Orientation
from pyte.layout import Container, Chain
from pyte.paragraph import ParagraphStyle, Paragraph, Justify
from pyte.text import StyledText
from pyte.text import Bold, Emphasized, SmallCaps
from pyte.text import boldItalicStyle
from pyte.math import MathFonts, MathStyle, Equation, EquationStyle
from pyte.math import Math as PyteMath
from pyte.structure import Heading, List, Reference
from pyte.structure import NumberingStyle, HeadingStyle, ListStyle
from pyte.bibliography import Bibliography, BibliographyFormatter


# use Gyre Termes instead of (PDF Core) Times
use_termes = False

# fonts
# ----------------------------------------------------------------------------
if use_termes:
    termes_roman = Font("fonts/qtmr")
    termes_bold = Font("fonts/qtmb")
    termes_italic = Font("fonts/qtmri")
    termes_bold_italic = Font("fonts/qtmbi")

    termes = TypeFace("TeXGyreTermes",
                      roman=termes_roman, bold=termes_bold,
                      italic=termes_italic, bolditalic=termes_bold_italic)

    ieeeFamily = TypeFamily(serif=termes)
else:
    from pyte.fonts.adobe14 import family as ieeeFamily

schola_roman = Font("fonts/qcsr")
schola_italic = Font("fonts/qcsri")
schola_bold = Font("fonts/qcsb")
heros_roman = Font("fonts/qhvr")
cursor_regular = Font("fonts/qcrr")
chorus = Font("fonts/qzcmi")
standard_symbols = Font("fonts/usyr")
cmex9 = Font("fonts/cmex9")

std_math = MathFonts(schola_roman, schola_italic, schola_bold,
                     heros_roman, cursor_regular, chorus, standard_symbols,
                     cmex9)

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

mathstyle = MathStyle('math', fonts=std_math)

equationstyle = EquationStyle('equation', base=bodyStyle,
                              math_style=mathstyle,
                              indentFirst=0*pt,
                              spaceAbove=6*pt,
                              spaceBelow=6*pt,
                              justify=Justify.Center)

bibliographyStyle = ParagraphStyle('bibliography', base=bodyStyle,
                                   fontSize=9*pt)

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

class Abstract(Paragraph):
    def __init__(self, text):
        label = StyledText("Abstract &mdash; ", boldItalicStyle)
        return super().__init__([label, text], abstractStyle)


class IndexTerms(Paragraph):
    def __init__(self, terms):
        label = StyledText("Index Terms &mdash; ", boldItalicStyle)
        text = ", ".join(sorted(terms)) + "."
        text = text.capitalize()
        return super().__init__([label, text], abstractStyle)


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
        for element in self.getchildren():
            if isinstance(element, Title):
                element.render(target, level=level, id=self.get('id', None))
            elif type(element) == Section:
                element.render(target, level=level + 1)
            else:
                element.render(target)


class Title(CustomElement):
    def render(self, target, level=1, id=None):
        #print('Title.render()')
        heading = Heading(self.text, style=heading_styles[level - 1],
                          level=level)
        if id:
            target.document.elements[id] = heading
        target.addParagraph(heading)
        # TODO: refactor addParagraph to add_block?


class P(CustomElement):
    def render(self, target):
        #print('P.render()')
        if self.text is not None:
            content = self.text
        else:
            content = ''
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
        return Emphasized(self.text)


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


class Math(CustomElement):
    def render(self, target):
        math = PyteMath(self.text, style=mathstyle)
        math.document = target.document
        return math


class Eq(CustomElement):
    def render(self, target, id=None):
        equation = Equation(self.text, style=equationstyle)
        equation.document = target.document # TODO: do this properly
        id = self.get('id', None)
        if id:
            target.document.elements[id] = equation
        return equation


class Cite(CustomElement):
    def render(self, target):
        #print('Cite.render()')
        # TODO: general document getter in TextTarget/Chain/Container
        return target.document.bibliography.cite(self.get('id'))


class Ref(CustomElement):
    def render(self, target):
        #print('Ref.render()')
        return Reference(self.get('id'), target)


class Acknowledgement(CustomElement):
    def render(self, target):
        #print('Acknowledgement.render()')
        heading = Heading('Acknowledgement',
                          style=acknowledgement_heading_style, level=1)
        target.addParagraph(heading)
        for element in self.getchildren():
            element.render(target)


# bibliography style
# ----------------------------------------------------------------------------

class IEEEBibliographyFormatter(BibliographyFormatter):
    def format_citation(self, reference):
        try:
            index = self.bibliography.index(reference)
            return StyledText('[{}]'.format(index + 1))
        except:
            return StyledText('[ERROR]')

    def format_bibliography(self, target):
        items = []
        heading = Heading('References', style=acknowledgement_heading_style)
        target.addParagraph(heading)
        for i, ref in enumerate(self.bibliography):
            authors = ['{} {}'.format(name.given_initials(), name.family)
                       for name in ref.author]
            authors = ', '.join(authors)
            item = '[{}]&nbsp;{}, "{}", '.format(i + 1, authors, ref.title)
            item += Emphasized(ref['container_title'])
            item += ', {}'.format(ref.issued.year)
            items.append(item)
            paragraph = Paragraph(item, style=bibliographyStyle)
            target.addParagraph(paragraph)


# pages and their layout
# ----------------------------------------------------------------------------

class RFICPage(Page):
    topmargin = bottommargin = 1.125*inch
    leftmargin = rightmargin = 0.85*inch
    column_spacing = 0.25*inch

    def __init__(self, document, first=False):
        super().__init__(document, Letter, Orientation.Portrait)
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

    def __init__(self, filename, bibliography_source):
        lookup = etree.ElementNamespaceClassLookup()
        namespace = lookup.get_namespace('http://www.mos6581.org/ns/rficpaper')
        namespace[None] = CustomElement
        namespace.update(dict([(cls.__name__.lower(), cls)
                               for cls in CustomElement.__subclasses__()]))

        Document.__init__(self, filename, self.rngschema, lookup)

        self.bibliography = Bibliography(bibliography_source,
                                         IEEEBibliographyFormatter())

        authors = [author.text for author in self.root.head.authors.author]
        if len(authors) > 1:
            self.author = ', '.join(authors[:-1]) + ', and ' + authors[-1]
        else:
            self.author = authors[0]
        self.title = self.root.head.title.text
        self.keywords = [term.text for term in self.root.head.indexterms.term]

        self.content = Chain(self)

        for font in (schola_roman, schola_italic, schola_bold, heros_roman,
                     cursor_regular, chorus, standard_symbols):
            self.psg_doc.add_font(font.psFont)

    def render(self, filename):
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

        self.bibliography.bibliography(self.content)

        Document.render(self, filename)

    def add_to_chain(self, chain):
        page = RFICPage(self)
        self.addPage(page)
        return page.column1
