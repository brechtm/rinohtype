
from rinoh.document import DocumentSection
from rinoh.paragraph import Paragraph

from .base import ContentsPart, DocumentBase, DocumentOptions


# document parts
# ----------------------------------------------------------------------------

class ArticlePart(ContentsPart):
    def new_page(self, chains):
        page = super().new_page(chains)
        if self.number_of_pages == 0:
            meta = self.document.metadata
            page.content << Paragraph(meta['title'], style='title')
            page.content << Paragraph(meta['subtitle'], style='subtitle')
            date = meta['date']
            try:
                page.content << Paragraph(date.strftime('%B %d, %Y'),
                                          style='author')
            except AttributeError:
                page.content << Paragraph(date, style='author')
            page.content << Paragraph(meta['author'], style='author')
        return page


class ArticleSection(DocumentSection):
    parts = [ArticlePart]


# main document
# ----------------------------------------------------------------------------

class ArticleOptions(DocumentOptions):
    pass


class Article(DocumentBase):
    sections = [ArticleSection]
    options_class = ArticleOptions
