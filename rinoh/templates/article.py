# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..attribute import Attribute, OptionSet, Bool, OverrideDefault, Var
from ..dimension import CM
from ..structure import TableOfContentsSection
from ..stylesheets import sphinx_article
from ..template import (DocumentTemplate, PageTemplate, TitlePageTemplate,
                        ContentsPartTemplate, TemplateConfiguration,
                        DocumentPartTemplate, TitlePartTemplate)


__all__ = ['Article', 'TITLE', 'FRONT_MATTER']


TITLE = 'title'
FRONT_MATTER = 'front_matter'


class AbstractLocation(OptionSet):
    """Where to place the article's abstract"""

    values = TITLE, FRONT_MATTER


class ArticleFrontMatter(DocumentPartTemplate):
    def flowables(self, document):
        meta = document.metadata
        abstract_loc = document.configuration.get_option('abstract_location')
        if 'abstract' in meta and abstract_loc == FRONT_MATTER:
            yield meta['abstract']
        if document.configuration.get_option('table_of_contents'):
            yield TableOfContentsSection()


class ArticleConfiguration(TemplateConfiguration):
    stylesheet = OverrideDefault(sphinx_article)
    table_of_contents = Attribute(Bool, True,
                                  'Show or hide the table of contents')
    abstract_location = Attribute(AbstractLocation, FRONT_MATTER,
                                  'Where to place the abstract')

    title_page = TitlePageTemplate(page_size=Var('paper_size'),
                                   top_margin=8*CM)
    page = PageTemplate(page_size=Var('paper_size'),
                        chapter_title_flowables=None)


class Article(DocumentTemplate):
    Configuration = ArticleConfiguration
    parts = [TitlePartTemplate('title', Configuration.title_page),
             ArticleFrontMatter('front matter', Configuration.page),
             ContentsPartTemplate('contents', Configuration.page)]
