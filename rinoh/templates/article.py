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


template_conf = TemplateConfiguration()


template_conf['title page'] = TitlePageTemplate(top_margin=8*CM)

template_conf['page'] = PageTemplate()


class ArticleTemplate(DocumentTemplate):
    template_configuration = template_conf
    parts = [FixedDocumentPartTemplate([], 'title page'),
             FixedDocumentPartTemplate([TableOfContentsSection()],
                                       'page'),
             ContentsPartTemplate('page')]
