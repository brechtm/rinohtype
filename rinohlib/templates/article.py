
from rinoh.document import DocumentSection
from rinoh.layout import Chain
from rinoh.paragraph import Paragraph
from rinoh.structure import GroupedFlowables

from .base import (ContentsPart, DocumentBase, DocumentOptions,
                   TableOfContentsSection)


class TitleFlowables(GroupedFlowables):
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


class ArticleFrontMatter(GroupedFlowables):
    def __init__(self):
        self.toc_section = TableOfContentsSection()
        super().__init__()

    def prepare(self, document):
        self.toc_section.prepare(document)

    def flowables(self, document):
        meta = document.metadata
        if 'abstract' in meta:
            yield meta['abstract']
        if document.options['table_of_contents']:
            yield self.toc_section


# document parts
# ----------------------------------------------------------------------------

class ArticlePart(ContentsPart):
    def __init__(self, document_section):
        self.front_matter = ArticleFrontMatter()
        super().__init__(document_section)
        self.title_flowables = TitleFlowables()

    def prepare(self):
        self.front_matter.prepare(self.document)

    def flowables(self):
        yield self.front_matter
        for flowable in super().flowables():
            yield flowable

    def first_page(self):
        return self.new_page([self.chain], title_flowables=self.title_flowables,
                             header=False)


class ArticleSection(DocumentSection):
    parts = [ArticlePart]


# main document
# ----------------------------------------------------------------------------

class ArticleOptions(DocumentOptions):
    options = {'table_of_contents': True}


class Article(DocumentBase):
    sections = [ArticleSection]
    options_class = ArticleOptions
