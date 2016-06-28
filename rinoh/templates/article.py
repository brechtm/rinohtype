# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.dimension import CM
from rinoh.structure import TableOfContentsSection
from rinoh.template import (DocumentTemplate, PageTemplate, TitlePageTemplate,
                            ContentsPartTemplate, FixedDocumentPartTemplate)


title_page_template = TitlePageTemplate(top_margin=8*CM)
page_template = PageTemplate()


class ArticleTemplate(DocumentTemplate):
    parts = [FixedDocumentPartTemplate([], title_page_template),
             FixedDocumentPartTemplate([TableOfContentsSection()],
                                       page_template),
             ContentsPartTemplate(page_template)]
