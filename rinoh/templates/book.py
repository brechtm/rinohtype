# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.dimension import INCH
from rinoh.index import IndexSection
from rinoh.number import NUMBER, ROMAN_LC
from rinoh.paper import A4
from rinoh.paragraph import Paragraph
from rinoh.reference import (Variable, Reference, PAGE_NUMBER, TITLE,
                             DOCUMENT_TITLE, DOCUMENT_SUBTITLE,
                             SECTION_NUMBER, SECTION_TITLE)
from rinoh.structure import TableOfContentsSection
from rinoh.template import (TitlePageTemplate, PageTemplate, DocumentTemplate,
                            FixedDocumentPartTemplate, ContentsPartTemplate,
                            TemplateConfiguration)
from rinoh.text import Tab


paper_size = A4

def front_matter_section_title_flowables(section_id):
    yield Paragraph(Reference(section_id, TITLE),
                    style='front matter section title')


def body_matter_chapter_title_flowables(section_id):
    yield Paragraph('CHAPTER ' + Reference(section_id, NUMBER, style='number'),
                    style='body matter chapter label')
    yield Paragraph(Reference(section_id, TITLE),
                    style='body matter chapter title')

template_conf = TemplateConfiguration()

template_conf['page'] = \
    PageTemplate(page_size=paper_size,
                 left_margin=1 * INCH,
                 right_margin=1 * INCH,
                 top_margin=1 * INCH,
                 bottom_margin=1 * INCH)

template_conf['title page'] = TitlePageTemplate(base='page')

template_conf['front matter right page'] = \
    PageTemplate(base='page',
                 header_footer_distance=0,
                 header_text=None,
                 footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_header_text=None,
                 chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_title_height=2.5 * INCH,
                 chapter_title_flowables=front_matter_section_title_flowables)

template_conf['front matter left page'] = \
    PageTemplate(base='page',
                 header_footer_distance=0,
                 header_text=None,
                 footer_text=Variable(PAGE_NUMBER))

template_conf['content right page'] = \
    PageTemplate(base='page',
                 header_footer_distance=0,
                 header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                              + ', ' + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(SECTION_NUMBER(2))
                              + '.  ' + Variable(SECTION_TITLE(2))
                              + Tab() + Tab() + Variable(PAGE_NUMBER)),
                 chapter_header_text=None,
                 chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_title_height=2.4 * INCH,
                 chapter_title_flowables=body_matter_chapter_title_flowables)

template_conf['content left page'] = \
    PageTemplate(base='page',
                 header_footer_distance=0,
                 header_text=(Variable(DOCUMENT_TITLE) + ', '
                              + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab() +
                              'Chapter ' + Variable(SECTION_NUMBER(1))
                              + '.  ' + Variable(SECTION_TITLE(1))))

template_conf['back matter right page'] = \
    PageTemplate(base='page',
                 columns=2,
                 header_footer_distance=0,
                 header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                              + ', ' + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(SECTION_TITLE(1))
                              + Tab() + Tab() + Variable(PAGE_NUMBER)),
                 chapter_header_text=None,
                 chapter_footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                 chapter_title_height=2.5 * INCH,
                 chapter_title_flowables=front_matter_section_title_flowables)

template_conf['back matter left page'] = \
    PageTemplate(base='page',
                 columns=2,
                 header_footer_distance=0,
                 header_text=(Variable(DOCUMENT_TITLE) + ', '
                              + Variable(DOCUMENT_SUBTITLE)),
                 footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab()
                              + Variable(SECTION_TITLE(1))))


class BookTemplate(DocumentTemplate):
    template_configuration = template_conf
    parts = [FixedDocumentPartTemplate([], 'title page'),
             FixedDocumentPartTemplate([TableOfContentsSection()],
                                       'front matter right page',
                                       'front matter left page',
                                       page_number_format=ROMAN_LC),
             ContentsPartTemplate('content right page',
                                  'content left page',
                                  page_number_format=NUMBER),
             FixedDocumentPartTemplate([IndexSection()],
                                       'back matter right page',
                                       'back matter left page')]
