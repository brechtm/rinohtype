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
from ..structure import TableOfContentsSection
from ..stylesheets import sphinx
from ..template import (TitlePageTemplate, PageTemplate, DocumentTemplate,
                        FixedDocumentPartTemplate, ContentsPartTemplate,
                        TemplateConfiguration, TitlePartTemplate)
from ..text import Tab


def front_matter_section_title_flowables(section_id):
    yield Paragraph(Reference(section_id, TITLE),
                    style='front matter section title')


def body_matter_chapter_title_flowables(section_id):
    yield Paragraph('CHAPTER ' + Reference(section_id, NUMBER, style='number'),
                    style='body matter chapter label')
    yield Paragraph(Reference(section_id, TITLE),
                    style='body matter chapter title')


class BookConfiguration(TemplateConfiguration):
    stylesheet = OverrideDefault(sphinx)
    page = \
        PageTemplate(page_size=Var('paper_size'),
                     left_margin=1 * INCH,
                     right_margin=1 * INCH,
                     top_margin=1 * INCH,
                     bottom_margin=1 * INCH)
    title_page = TitlePageTemplate(base='page')
    front_matter_right_page = \
        PageTemplate(base='page',
                     header_footer_distance=0,
                     header_text=None,
                     footer_text=Tab() + Tab() + Variable(PAGE_NUMBER),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab()
                                         + Variable(PAGE_NUMBER),
                     chapter_title_height=2.5 * INCH,
                     chapter_title_flowables=
                     front_matter_section_title_flowables)
    front_matter_left_page = \
        PageTemplate(base='page',
                     header_footer_distance=0,
                     header_text=None,
                     footer_text=Variable(PAGE_NUMBER))
    content_right_page = \
        PageTemplate(base='page',
                     header_footer_distance=0,
                     header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                                  + ', ' + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(SECTION_NUMBER(2))
                                  + '.  ' + Variable(SECTION_TITLE(2))
                                  + Tab() + Tab() + Variable(PAGE_NUMBER)),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab()
                                         + Variable(PAGE_NUMBER),
                     chapter_title_height=2.4 * INCH,
                     chapter_title_flowables=
                     body_matter_chapter_title_flowables)
    content_left_page = \
        PageTemplate(base='page',
                     header_footer_distance=0,
                     header_text=(Variable(DOCUMENT_TITLE) + ', '
                                  + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab() +
                                  'Chapter ' + Variable(SECTION_NUMBER(1))
                                  + '.  ' + Variable(SECTION_TITLE(1))))

    back_matter_right_page = \
        PageTemplate(base='page',
                     columns=2,
                     header_footer_distance=0,
                     header_text=(Tab() + Tab() + Variable(DOCUMENT_TITLE)
                                  + ', ' + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(SECTION_TITLE(1))
                                  + Tab() + Tab() + Variable(PAGE_NUMBER)),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab()
                                         + Variable(PAGE_NUMBER),
                     chapter_title_height=2.5 * INCH,
                     chapter_title_flowables=
                     front_matter_section_title_flowables)

    back_matter_left_page = \
        PageTemplate(base='page',
                     columns=2,
                     header_footer_distance=0,
                     header_text=(Variable(DOCUMENT_TITLE) + ', '
                                  + Variable(DOCUMENT_SUBTITLE)),
                     footer_text=(Variable(PAGE_NUMBER) + Tab() + Tab()
                                  + Variable(SECTION_TITLE(1))))


class Book(DocumentTemplate):
    Configuration = BookConfiguration
    parts = [TitlePartTemplate('title', Configuration.title_page),
             FixedDocumentPartTemplate('front matter',
                                       [TableOfContentsSection()],
                                       Configuration.front_matter_right_page,
                                       Configuration.front_matter_left_page,
                                       page_number_format=ROMAN_LC),
             ContentsPartTemplate('contents',
                                  Configuration.content_right_page,
                                  Configuration.content_left_page,
                                  page_number_format=NUMBER),
             FixedDocumentPartTemplate('indices', [IndexSection()],
                                       Configuration.back_matter_right_page,
                                       Configuration.back_matter_left_page)]
