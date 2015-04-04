
from rinoh.document import DocumentSection
from rinoh.paragraph import Paragraph
from rinoh.structure import GroupedFlowables, Section, Heading, TableOfContents

from .base import ContentsPart, DocumentBase, DocumentOptions


class ArticleFrontMatter(GroupedFlowables):
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


# document parts
# ----------------------------------------------------------------------------

class ArticlePart(ContentsPart):
    def flowables(self):
        yield ArticleFrontMatter()
        if self.document.options['table_of_contents']:
            yield Section([Heading('Table of Contents', style='unnumbered'),
                           TableOfContents()],
                          style='table of contents')
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
