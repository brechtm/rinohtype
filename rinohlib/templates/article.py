
from rinoh.document import DocumentSection
from rinoh.paragraph import Paragraph
from rinoh.structure import GroupedFlowables

from .base import (ContentsPart, DocumentBase, DocumentOptions,
                   TableOfContentsSection)


class ArticleFrontMatter(GroupedFlowables):
    def __init__(self):
        self.toc_section = TableOfContentsSection()
        super().__init__()
    def flowables(self, document):
        meta = document.metadata
        yield Paragraph(meta['title'], style='title')
        if 'subtitle' in meta:
            yield Paragraph(meta['subtitle'], style='subtitle')
        if 'date' in meta:
            date = meta['date']
            try:
                yield Paragraph(date.strftime('%B %d, %Y'), style='author')
            except AttributeError:
                yield Paragraph(date, style='author')
        if 'author' in meta:
            yield Paragraph(meta['author'], style='author')
        if document.options['table_of_contents']:
            yield self.toc_section


# document parts
# ----------------------------------------------------------------------------

class ArticlePart(ContentsPart):
    def __init__(self, document_section):
        self.front_matter = ArticleFrontMatter()
        super().__init__(document_section)

    def flowables(self):
        yield self.front_matter
        for flowable in super().flowables():
            yield flowable


class ArticleSection(DocumentSection):
    parts = [ArticlePart]


# main document
# ----------------------------------------------------------------------------

class ArticleOptions(DocumentOptions):
    options = {'table_of_contents': True}


class Article(DocumentBase):
    sections = [ArticleSection]
    options_class = ArticleOptions
