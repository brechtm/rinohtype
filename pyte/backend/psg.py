
from psg.document.dsc import dsc_document
from psg.drawing.box import canvas as psg_Canvas


class Document(object):
    def __init__(self, title):
        self.psg_doc = dsc_document(title)

    def new_page(self, width, height):
        psg_page = self.psg_doc.page((float(width), float(height)))
        return Page(psg_page)

    def write(self, filename):
        fp = open(filename, "w", encoding="latin-1")
        self.psg_doc.write_to(fp)
        fp.close()


class Page(object):
    def __init__(self, psg_page):
        self.psg_page = psg_page
        self.canvas = PageCanvas(psg_page.canvas(), self)


class Canvas(object):
    def __init__(self, parent, left, bottom, width, height, clip=False):
        self.parent = parent
        self.psg_canvas = psg_Canvas(parent.psg_canvas,
                                     left, bottom, width, height, clip=clip)

    @property
    def width(self):
        return self.psg_canvas.w()

    @property
    def height(self):
        return self.psg_canvas.h()

    def new(self, left, bottom, width, height, clip=False):
        new_canvas = Canvas(self, left, bottom, width, height, clip)
        return new_canvas

    def append(self, canvas):
        self.psg_canvas.append(canvas.psg_canvas)

    def append_new(self, left, bottom, width, height, clip=False):
        new_canvas = self.new(left, bottom, width, height, clip)
        self.append(new_canvas)
        return new_canvas

    def translate(self, x, y):
        print('{0} {1} moveto'.format(x, y), file=self.psg_canvas)

    def select_font(self, font, size):
        self.font_wrapper = self.psg_canvas.page.register_font(font.psFont,
                                                               True)
        print('/{0} findfont'.format(self.font_wrapper.ps_name()),
                                     file=self.psg_canvas)
        print('{0} scalefont'.format(size), file=self.psg_canvas)
        print('setfont', file=self.psg_canvas)

    def show_glyphs(self, characters, x_displacements):
        try:
            ps_repr = self.font_wrapper.postscript_representation(characters)
        except AttributeError:
            raise RuntimeError('No font selected for canvas.')
        widths = ' '.join(map(lambda f: '%.2f' % f, x_displacements))
        print('({0}) [{1}] xshow'.format(ps_repr, widths), file=self.psg_canvas)


class PageCanvas(Canvas):
    def __init__(self, psg_canvas, page):
        self.psg_canvas = psg_canvas
        self.page = page
