from rinoh.dimension import PERCENT
from rinoh.float import InlineImage
from rinoh.paper import A4
from rinoh.backend import pdf
from rinoh.frontend.dita import DITAReader
from rinoh.reference import Variable, SECTION_TITLE, PAGE_NUMBER
from rinoh.text import Tab

from rinohlib.templates.article import Article, ArticleOptions, TITLE
from rinohlib.stylesheets.sphinx import stylesheet


HEADER_TEXT = 'About RinohType' + Tab() + Tab() + Variable(SECTION_TITLE(1))
FOOTER_TEXT = (InlineImage('company_logo.pdf',
                           scale=0.7, baseline=31.5*PERCENT)
               + Tab() + Tab() + 'page ' + Variable(PAGE_NUMBER))


OPTIONS = ArticleOptions(page_size=A4, table_of_contents=True)
OPTIONS = ArticleOptions(page_size=A4, columns=2, table_of_contents=True,
                         header_text=HEADER_TEXT, footer_text=FOOTER_TEXT,
                         stylesheet=stylesheet, abstract_location=TITLE,
                         show_date=False, show_author=False)


if __name__ == '__main__':
    reader = DITAReader()
    for name in ('sequence', 'hierarchy'):
        with open(name + '.ditamap') as file:
            flowables = reader.parse(file)
        document = Article(flowables, options=OPTIONS, backend=pdf)
        document.render(name)
