# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.dimension import CM
from rinoh.structure import TableOfContentsSection
from rinoh.template import (DocumentTemplate, PageTemplate, TitlePageTemplate,
                            ContentsPartTemplate, FixedDocumentPartTemplate,
                            TemplateConfiguration)


__all__ = ['Article']


class Article(DocumentTemplate):

    class Configuration(TemplateConfiguration):
        title_page = TitlePageTemplate(top_margin=8*CM)
        page = PageTemplate()

    parts = [FixedDocumentPartTemplate([], Configuration.title_page),
             FixedDocumentPartTemplate([TableOfContentsSection()],
                                       Configuration.page),
             ContentsPartTemplate(Configuration.page)]
