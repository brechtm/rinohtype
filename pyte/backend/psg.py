
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

    def append(self, canvas):
        self.psg_canvas.append(canvas.psg_canvas)

    def append_new(self, left, bottom, width, height, clip=False):
        new_canvas = Canvas(self, left, bottom, width, height, clip)
        self.append(new_canvas)
        return new_canvas


class PageCanvas(Canvas):
    def __init__(self, psg_canvas, page):
        self.psg_canvas = psg_canvas
        self.page = page
