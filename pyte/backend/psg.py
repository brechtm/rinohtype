
from psg.document.dsc import dsc_document
from psg.drawing.box import canvas as psg_Canvas


class Document(object):
    def __init__(self, pyte_document, title):
        self.pyte_document = pyte_document
        self.psg_doc = dsc_document(title)

    def write(self, filename):
        fp = open(filename, "w", encoding="latin-1")
        self.psg_doc.write_to(fp)
        fp.close()


class Page(object):
    def __init__(self, pyte_page, psg_document, width, height):
        self.pyte_page = pyte_page
        self.psg_doc = psg_document
        self.psg_page = psg_document.psg_doc.page((float(width), float(height)))
        self.canvas = PageCanvas(self, self.psg_page.canvas())

    @property
    def document(self):
        return self.pyte_page.document


class Canvas(object):
    def __init__(self, parent, left, bottom, width, height, clip=False):
        self.parent = parent
        self.psg_canvas = psg_Canvas(parent.psg_canvas,
                                     left, bottom, width, height, clip=clip)

    @property
    def page(self):
        return self.parent.page

    @property
    def document(self):
        return self.page.document

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

    def save_state(self):
        print('gsave', file=self.psg_canvas)

    def restore_state(self):
        print('grestore', file=self.psg_canvas)

    def translate(self, x, y):
        print('{0} {1} translate'.format(x, y), file=self.psg_canvas)

    def scale(self, x, y=None):
        if y is None:
            y = x
        print('{0} {1} scale'.format(x, y), file=self.psg_canvas)

    def move_to(self, x, y):
        print('{0} {1} moveto'.format(x, y), file=self.psg_canvas)

    def line_to(self, x, y):
        print('{0} {1} lineto'.format(x, y), file=self.psg_canvas)

    def new_path(self):
        print('newpath', file=self.psg_canvas)

    def close_path(self):
        print('closepath', file=self.psg_canvas)

    def line_path(self, points):
        self.new_path()
        self.move_to(*points[0])
        for point in points[1:]:
            self.line_to(*point)
        self.close_path()

    def line_width(self, width):
        print('{0} setlinewidth'.format(width), file=self.psg_canvas)

    def color(self, color):
        r, g, b, a = color.rgba
        print('{0} {1} {2} setrgbcolor'.format(r, g, b), file=self.psg_canvas)

    def stroke(self, linewidth, color):
        self.save_state()
        self.color(color)
        self.line_width(float(linewidth))
        print('stroke', file=self.psg_canvas)
        self.restore_state()

    def fill(self):
        self.save_state()
        self.color(color)
        print('fill', file=self.psg_canvas)
        self.restore_state()

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
    def __init__(self, page, psg_canvas):
        self.parent = page
        self.psg_canvas = psg_canvas

    @property
    def page(self):
        return self.parent.pyte_page
