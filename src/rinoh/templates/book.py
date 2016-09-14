# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..attribute import OverrideDefault, Var
from ..dimension import INCH
from ..index import IndexSection
from ..number import NUMBER, ROMAN_LC
from ..paragraph import Paragraph
from ..reference import (Variable, Reference, PAGE_NUMBER, TITLE,
                         DOCUMENT_TITLE, DOCUMENT_SUBTITLE,
                         SECTION_NUMBER, SECTION_TITLE)
from ..strings import StringField
from ..structure import TableOfContentsSection, SectionTitles
from ..stylesheets import sphinx
from ..template import (TitlePageTemplate, PageTemplate, DocumentTemplate,
                        FixedDocumentPartTemplate, ContentsPartTemplate,
                        TemplateConfiguration, TitlePartTemplate,
                        DocumentPartTemplate)
from ..text import Tab


def front_matter_section_title_flowables(section_id):
    yield Paragraph(Reference(section_id, TITLE, link=False),
                    style='front matter section title')


def body_matter_chapter_title_flowables(section_id):
    yield Paragraph(StringField(SectionTitles, 'chapter').upper() + ' '
                    + Reference(section_id, NUMBER, link=False,
                                style='number'),
                    style='body matter chapter label')
    yield Paragraph(Reference(section_id, TITLE, link=False),
                    style='body matter chapter title')


class BookBackMatter(DocumentPartTemplate):
    index_section = IndexSection()

    def flowables(self, document):
        if document.index_entries:
            yield self.index_section


class BookConfiguration(TemplateConfiguration):
    stylesheet = OverrideDefault(sphinx)


class Book(DocumentTemplate):
    Configuration = BookConfiguration
    parts = [TitlePartTemplate('title'),
             FixedDocumentPartTemplate('front matter',
                                       [TableOfContentsSection()]),
             ContentsPartTemplate('contents'),
             BookBackMatter('back matter')]


# default page templates

BookConfiguration['page'] = \
    PageTemplate(page_size=Var('paper_size'),
                 left_margin=1*INCH,
                 right_margin=1*INCH,
                 top_margin=1*INCH,
                 bottom_margin=1*INCH)

BookConfiguration['title:page'] = TitlePageTemplate(base='page')

BookConfiguration['front matter:page'] = \
    PageTemplate(base='page',
                 header_footer_distance=0,
                 header_text=None)

BookConfiguration['front matter:right page'] = \
    PageTemplate(base='front matter:page',
                 footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_header_text=None,
                 chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_title_height=2.5*INCH,
                 chapter_title_flowables=front_matter_section_title_flowables)

BookConfiguration['front matter:left page'] = \
    PageTemplate(base='front matter:page',
                 footer_text=Variable(PAGE_NUMBER))

BookConfiguration['contents:page'] = \
    PageTemplate(base='page',
                 header_footer_distance=0)

BookConfiguration['contents:right page'] = \
    PageTemplate(base='contents:page',
                 header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                              + ', ' + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(SECTION_NUMBER(2))
                              + '.  ' + Variable(SECTION_TITLE(2))
                              + Tab() + Tab() + Variable(PAGE_NUMBER)),
                 chapter_header_text=None,
                 chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_title_height=2.4*INCH,
                 chapter_title_flowables=body_matter_chapter_title_flowables)

BookConfiguration['contents:left page'] = \
    PageTemplate(base='contents:page',
                 header_text=(Variable(DOCUMENT_TITLE) + ', '
                              + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab() +
                              StringField(SectionTitles, 'chapter')
                              + ' ' + Variable(SECTION_NUMBER(1))
                              + '.  ' + Variable(SECTION_TITLE(1))))

BookConfiguration['back matter:page'] = \
    PageTemplate(base='page',
                 columns=2,
                 header_footer_distance=0)

BookConfiguration['back matter:right page'] = \
    PageTemplate(base='back matter:page',
                 header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                              + ', ' + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(SECTION_TITLE(1))
                              + Tab() + Tab() + Variable(PAGE_NUMBER)),
                 chapter_header_text=None,
                 chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_title_height=2.5*INCH,
                 chapter_title_flowables=front_matter_section_title_flowables)

BookConfiguration['back matter:left page'] = \
    PageTemplate(base='back matter:page',
                 header_text=(Variable(DOCUMENT_TITLE) + ', '
                              + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab()
                              + Variable(SECTION_TITLE(1))))
