
from time import strptime, strftime

from rinoh.layout import Container, Chain
from rinoh.dimension import CM, PT, PERCENT
from rinoh.document import Document, Page, LANDSCAPE
from rinoh.paper import A4
from rinoh.style import StyleSheet, StyledMatcher
from rinoh.backend import pdf
from rinoh.paragraph import Paragraph
from rinoh.styles import ParagraphStyle
from rinoh.annotation import AnnotatedText, HyperLink
from rinoh.float import Image

from rinoh.text import BOLD

from rinohlib.fonts.texgyre.pagella import typeface as pagella


SAMPLE_INPUT = dict(artist='Terry Artist',
                    title='Lakeside',
                    year=1998,
                    editions=(1, 10),
                    status='Loaning',
                    owner=('John Artist', 'john@artist.com'),
                    crypto_id='jisadf8734hf83hsdfjklshdf3',
                    ownership_history=[('2014/11/13 07:11',
                                        'John Artist', 'john@artist.com')],
                    loan_history=[('2014/11/13 11:11',
                                   'John Artist', 'larry@gallery.com')])

DATETIME_IN_FMT = '%Y/%m/%d %H:%M'

DATETIME_OUT_FMT = '%b. %d, %Y, %I:%M %p'


MATCHER = StyledMatcher()
MATCHER['default'] = Paragraph
MATCHER['artist'] = Paragraph.like('artist')
MATCHER['title'] = Paragraph.like('title')
MATCHER['section title'] = Paragraph.like('section title')
MATCHER['image'] = Image


STYLESHEET = StyleSheet('ascribe', matcher=MATCHER)
STYLESHEET['default'] = ParagraphStyle(typeface=pagella,
                                       font_size=12*PT,
                                       space_below=6*PT,
                                       )
STYLESHEET['artist'] = ParagraphStyle(base='default',
                                      font_size=14*PT,
                                      )
STYLESHEET['title'] = ParagraphStyle(base='default',
                                     font_weight=BOLD,
                                     font_size=18*PT,
                                     space_below=10*PT,
                                     )

STYLESHEET['section title'] = ParagraphStyle(base='default',
                                             font_weight=BOLD,
                                             font_size=16*PT,
                                             space_below=8*PT,
                                             )


class AscribePage(Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM
    left_column_width = 10*CM
    column_spacing = 1*CM

    def __init__(self, document):
        super().__init__(document, A4, LANDSCAPE)
        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        body = Container('body', self, self.leftmargin, self.topmargin,
                         body_width, body_height)

        self.column1 = Container('column1', body, 0*PT, 0*PT,
                                 width=self.left_column_width,
                                 chain=document.image)
        self.column2 = Container('column2', body,
                                 self.left_column_width + self.column_spacing,
                                 chain=document.text)


class AscribeCertificate(Document):
    namespace = 'http://www.mos6581.org/ns/rficpaper'

    def __init__(self):
        title = ' - '.join((SAMPLE_INPUT['artist'], SAMPLE_INPUT['title']))
        super().__init__(STYLESHEET, backend=pdf, title=title)
        self.image = Chain(self)
        self.image << Image('image', width=100*PERCENT)

        self.text = Chain(self)
        self.text << Paragraph(SAMPLE_INPUT['artist'], style='artist')
        self.text << Paragraph(SAMPLE_INPUT['title'], style='title')
        self.text << Paragraph(str(SAMPLE_INPUT['year']), style='default')
        nr_edition, total_editions = SAMPLE_INPUT['editions']
        self.text << Paragraph('Editions: {}/{}'.format(nr_edition,
                                                        total_editions),
                               style='default')
        self.text << Paragraph('Status: ' + SAMPLE_INPUT['status'],
                               style='default')
        owner_name, owner_email = SAMPLE_INPUT['owner']
        email_link = AnnotatedText(owner_email,
                                   annotation=HyperLink('mailto:' + owner_email))
        self.text << Paragraph('Owner: ' + owner_name + ', ' + email_link,
                               style='default')
        self.text << Paragraph('Crypto ID: ' +
                               SAMPLE_INPUT['crypto_id'], style='default')

        self.text << Paragraph('Provenance/Ownership History',
                               style='section title')
        self._history(SAMPLE_INPUT['ownership_history'],
                      'ownership ascribed to')

        self.text << Paragraph('Consignment/Loan History',
                               style='section title')
        self._history(SAMPLE_INPUT['loan_history'], 'loaned to')

    def _history(self, items, action):
        for dtime_str, name, email in items:
            dtime = strptime(dtime_str, DATETIME_IN_FMT)
            self.text << Paragraph(strftime(DATETIME_OUT_FMT, dtime) +
                                   ' ' + action + ' ' + name + ', ' + email)

    def setup(self):
        page = AscribePage(self)
        self.add_page(page, 1)


if __name__ == '__main__':
    certificate = AscribeCertificate()
    certificate.render('test')
