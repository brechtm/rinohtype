# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..attribute import Attribute, OptionSet, Bool, OverrideDefault, Var
from ..dimension import CM
from ..document import DocumentPart
from ..structure import TableOfContentsSection
from ..stylesheets import sphinx_article
from ..template import (DocumentTemplate, PageTemplate, TitlePageTemplate,
                        ContentsPartTemplate, FixedDocumentPartTemplate,
                        TemplateConfiguration, DocumentPartTemplate)


__all__ = ['Article', 'TITLE', 'FRONT_MATTER']


TITLE = 'title'
FRONT_MATTER = 'front_matter'


class AbstractLocation(OptionSet):
    values = TITLE, FRONT_MATTER


class ArticleFrontMatter(DocumentPartTemplate):
    def document_part(self, document_section):
        document = document_section.document
        meta = document.metadata
        abstract_loc = document.configuration.get_option('abstract_location')
        flowables = []
        if 'abstract' in meta and abstract_loc == FRONT_MATTER:
            flowables.append(meta['abstract'])
        if document.configuration.get_option('table_of_contents'):
            flowables.append(TableOfContentsSection())
        if flowables:
            return DocumentPart(document_section,
                                self.page_template, self.left_page_template,
                                flowables)


class Article(DocumentTemplate):

    class Configuration(TemplateConfiguration):
        stylesheet = OverrideDefault(sphinx_article)
        table_of_contents = Attribute(Bool, True,
                                      'Show or hide the table of contents')
        abstract_location = Attribute(AbstractLocation, FRONT_MATTER,
                                      'Where to place the abstract')

        title_page = TitlePageTemplate(page_size=Var('paper_size'),
                                       top_margin=8*CM)
        page = PageTemplate(page_size=Var('paper_size'),
                            chapter_title_flowables=None)

    parts = [FixedDocumentPartTemplate([], Configuration.title_page),
             ArticleFrontMatter(Configuration.page),
             ContentsPartTemplate(Configuration.page)]
