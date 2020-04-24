# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..attribute import OverrideDefault, Var
from ..dimension import INCH
from ..image import ListOfFiguresSection
from ..index import IndexSection
from ..paragraph import Paragraph
from ..reference import (Field, PAGE_NUMBER, DOCUMENT_TITLE, DOCUMENT_SUBTITLE,
                         SECTION_NUMBER, SECTION_TITLE)
from ..strings import StringField
from ..structure import TableOfContentsSection, SectionTitles
from ..stylesheets import sphinx
from ..table import ListOfTablesSection
from ..template import (TitlePageTemplate, PageTemplate, DocumentTemplate,
                        FixedDocumentPartTemplate, ContentsPartTemplate,
                        TitlePartTemplate, DocumentPartTemplate)
from ..text import Tab


FRONT_MATTER_TITLE = [Paragraph(Field(SECTION_TITLE(1)),
                                style='front matter section title')]


BODY_TITLE = [Paragraph(StringField(SectionTitles, 'chapter') + ' '
                        + Field(SECTION_NUMBER(1), style='number'),
                        style='body matter chapter label'),
              Paragraph(Field(SECTION_TITLE(1)),
                        style='body matter chapter title')]


class BackMatterTemplate(DocumentPartTemplate):
    index_section = IndexSection()

    def _flowables(self, document):
        if document.index_entries:
            yield self.index_section


class Book(DocumentTemplate):
    stylesheet = OverrideDefault(sphinx)

    parts = OverrideDefault(['title', 'front_matter',
                             'contents', 'back_matter'])

    # default document part templates
    cover = FixedDocumentPartTemplate(drop_if_empty=False,
                                      page_number_format=None,
                                      end_at_page='left')
    title = TitlePartTemplate(page_number_format='number',
                              end_at_page='left')
    front_matter = FixedDocumentPartTemplate(
                       flowables=[TableOfContentsSection(),
                                  ListOfFiguresSection(),
                                  ListOfTablesSection()],
                       page_number_format='lowercase roman',
                       end_at_page='left')
    contents = ContentsPartTemplate(page_number_format='number',
                                    end_at_page='left')
    back_matter = BackMatterTemplate(page_number_format='number',
                                     end_at_page='left')

    # default page templates
    page =  \
        PageTemplate(page_size=Var('paper_size'),
                     left_margin=1*INCH,
                     right_margin=1*INCH,
                     top_margin=1*INCH,
                     bottom_margin=1*INCH)

    cover_page = PageTemplate(base='page')
    title_page = TitlePageTemplate(base='page')
    
    front_matter_page =  \
        PageTemplate(base='page',
                     header_footer_distance=0,
                     header_text=None)
    
    front_matter_right_page =  \
        PageTemplate(base='front_matter_page',
                     footer_text=Tab() + Tab() + Field(PAGE_NUMBER),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab() + Field(PAGE_NUMBER),
                     chapter_title_height=2.5*INCH,
                     chapter_title_flowables=FRONT_MATTER_TITLE)
    
    front_matter_left_page =  \
        PageTemplate(base='front_matter_page',
                     footer_text=Field(PAGE_NUMBER))
    
    contents_page =  \
        PageTemplate(base='page',
                     header_footer_distance=0)
    
    contents_right_page =  \
        PageTemplate(base='contents_page',
                     header_text=(Tab() + Tab() + Field(DOCUMENT_TITLE)
                                  + ', ' + Field(DOCUMENT_SUBTITLE)),
                     footer_text=(Field(SECTION_NUMBER(2))
                                  + '.  ' + Field(SECTION_TITLE(2))
                                  + Tab() + Tab() + Field(PAGE_NUMBER)),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab() + Field(PAGE_NUMBER),
                     chapter_title_height=2.4*INCH,
                     chapter_title_flowables=BODY_TITLE)
    
    contents_left_page = \
        PageTemplate(base='contents_page',
                     header_text=(Field(DOCUMENT_TITLE) + ', '
                                  + Field(DOCUMENT_SUBTITLE)),
                     footer_text=(Field(PAGE_NUMBER) + Tab() + Tab() +
                                  StringField(SectionTitles, 'chapter')
                                  + ' ' + Field(SECTION_NUMBER(1))
                                  + '.  ' + Field(SECTION_TITLE(1))))
    
    back_matter_page = \
        PageTemplate(base='page',
                     columns=2,
                     header_footer_distance=0)
    
    back_matter_right_page = \
        PageTemplate(base='back_matter_page',
                     header_text=(Tab() + Tab() + Field(DOCUMENT_TITLE)
                                  + ', ' + Field(DOCUMENT_SUBTITLE)),
                     footer_text=(Field(SECTION_TITLE(1))
                                  + Tab() + Tab() + Field(PAGE_NUMBER)),
                     chapter_header_text=None,
                     chapter_footer_text=Tab() + Tab() + Field(PAGE_NUMBER),
                     chapter_title_height=2.5*INCH,
                     chapter_title_flowables=FRONT_MATTER_TITLE)
    
    back_matter_left_page = \
        PageTemplate(base='back_matter_page',
                     header_text=(Field(DOCUMENT_TITLE) + ', '
                                  + Field(DOCUMENT_SUBTITLE)),
                     footer_text=(Field(PAGE_NUMBER) + Tab() + Tab()
                                  + Field(SECTION_TITLE(1))))
