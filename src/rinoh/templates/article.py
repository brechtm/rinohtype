# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from contextlib import suppress
from functools import partial

from ..attribute import Attribute, Bool, OverrideDefault, Var
from ..dimension import CM, PT, Dimension
from ..layout import DownExpandingContainer, CONTENT
from ..paragraph import Paragraph
from ..structure import TableOfContentsSection
from ..stylesheets import sphinx_article
from ..template import (DocumentTemplate, BodyPageTemplateBase,
                        ContentsPartTemplate, BodyPage, try_copy, Option)
from ..text import StyledText


__all__ = ['Article']


class ArticleContentsPartTemplate(ContentsPartTemplate):
    toc_section = TableOfContentsSection()

    def _flowables(self, document):
        if document.get_option('table_of_contents'):
            yield self.toc_section
        yield from super()._flowables(document)


class ArticleBodyPageTemplate(BodyPageTemplateBase):
    title_spacing = Option(Dimension, 12*PT, 'Vertical spacing between the'
                                             '  title and the body text')
    title_page_header_text = Option(StyledText, None, 'The text to place in the'
                                    ' header on the title page')
    title_page_footer_text = Option(StyledText,
                                    BodyPageTemplateBase.footer_text.default_value,
                                    'The text to place in the footer on the'
                                    ' title page')

    def page(self, document_part, page_number, chain):
        return ArticleBodyPage(document_part, self, page_number, chain)


class ArticleBodyPage(BodyPage):
    configuration_class = ArticleBodyPageTemplate

    def get_header_footer_contenttop(self):
        if self.number > 1:
            return super().get_header_footer_contenttop()

        self.title = DownExpandingContainer('title', CONTENT, self.body, 0, 0)
        metadata = self.document.metadata
        p = lambda key, style: Paragraph(metadata[key], style=style)
        if 'title' in metadata:
            self.title << p('title', 'title page title')
        if 'subtitle' in metadata:
            self.title << p('subtitle', 'title page subtitle')
        if 'author' in metadata:
            self.title << p('author', 'title page author')
        with suppress(KeyError):
            self.title << metadata['abstract']

        header = try_copy(self.get_option('title_page_header_text'))
        footer = try_copy(self.get_option('title_page_footer_text'))
        return (header, footer,
                self.title.bottom + self.get_option('title_spacing'))


class Article(DocumentTemplate):
    stylesheet = OverrideDefault(sphinx_article)
    table_of_contents = Attribute(Bool, True,
                                  'Show or hide the table of contents')

    parts = OverrideDefault(['contents'])

    # default document part templates
    contents = ArticleContentsPartTemplate(page_number_format='number')

    # default page templates
    page = ArticleBodyPageTemplate(page_size=Var('paper_size'),
                                   left_margin=1.2*CM,
                                   right_margin=1.2*CM,
                                   top_margin=1.8*CM,
                                   bottom_margin=1.6*CM,
                                   header_footer_distance=2*PT)
    contents_page = ArticleBodyPageTemplate(base='page')
