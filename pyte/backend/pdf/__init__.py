
from io import StringIO
from . import cos
from .reader import PDFReader


class Document(object):
    extension = '.pdf'

    def __init__(self, pyte_document, title):
        self.pyte_document = pyte_document
        self.pdf_document = cos.Document()
        self.pages = []
        self.fonts = {}

    def register_font(self, font):
        try:
            font_rsc = self.fonts[font]
        except KeyError:
            assert font.is_core()
            font_rsc = cos.Font(self.pdf_document)
            font_rsc['Subtype'] = cos.Name('Type1')
            font_rsc['BaseFont'] = cos.Name(font.name)
            font_rsc['Encoding'] = cos.FontEncoding()
            self.fonts[font] = font_rsc
        return font_rsc

    def write(self, filename):
        for page in self.pages:
            contents = cos.Stream()
            contents.write(page.canvas.getvalue().encode('utf_8'))
            page.pdf_page['Contents'] = contents
        file = open(filename + self.extension, 'wb')
        self.pdf_document.write(file)
        file.close()


class Page(object):
    def __init__(self, pyte_page, document, width, height):
        self.pyte_page = pyte_page
        pdf_pages = document.pdf_document.catalog['Pages']
        self.pdf_page = pdf_pages.new_page(float(width), float(height))
        self.width = width
        self.height = height
        self.canvas = PageCanvas(self)
        document.pages.append(self)
        self.font_number = 1
        self.font_names = {}

    @property
    def document(self):
        return self.pyte_page.document

    def register_font(self, font):
        try:
            font_rsc, name = self.font_names[font]
        except KeyError:
            font_rsc = self.document.backend_document.register_font(font)
            name = 'F{}'.format(self.font_number)
            self.font_number += 1
            page_rsc = self.pdf_page['Resources']
            fonts_dict = page_rsc.setdefault('Font', cos.Dictionary())
            fonts_dict[name] = font_rsc
            self.font_names[font] = font_rsc, name
        return font_rsc, name


class Canvas(StringIO):
    def __init__(self, parent, left, bottom, width, height, clip=False):
        super().__init__()
        self.parent = parent
        self.left = left
        self.bottom = bottom
        self.width = width
        self.height = height
        self.translate(left, bottom)

    @property
    def page(self):
        return self.parent.page

    @property
    def pdf_page(self):
        return self.parent.page.backend_page

    @property
    def document(self):
        return self.page.document

    def new(self, left, bottom, width, height, clip=False):
        return Canvas(self, left, bottom, width, height, clip)

    def append(self, canvas):
        self.save_state()
        self.write(canvas.getvalue())
        self.restore_state()

    def save_state(self):
        print('q', file=self)

    def restore_state(self):
        print('Q', file=self)

    def translate(self, x, y):
        print('1 0 0 1 {} {} cm'.format(x, y), file=self)

    def scale(self, x, y=None):
        if y is None:
            y = x
        print('{} 0 0 {} 0 0 cm'.format(x, y), file=self)

    def move_to(self, x, y):
        print('{} {} m'.format(x, y), file=self)

    def line_to(self, x, y):
        print('{} {} l'.format(x, y), file=self)

    def new_path(self):
        pass

    def close_path(self):
        print('h', file=self)

    def line_path(self, points):
        self.new_path()
        self.move_to(*points[0])
        for point in points[1:]:
            self.line_to(*point)
        self.close_path()

    def line_width(self, width):
        print('{0} w'.format(width), file=self)

    def color(self, color):
        r, g, b, a = color.rgba
        #print('{0} {1} {2} setrgbcolor'.format(r, g, b), file=self)

    def stroke(self, linewidth=None, color=None):
        self.save_state()
        if color:
            self.color(color)
        if linewidth:
            self.line_width(float(linewidth))
        print('s', file=self)
        self.restore_state()

    def fill(self, color=None):
        self.save_state()
        if color:
            self.color(color)
        print('f', file=self)
        self.restore_state()

    def show_glyphs(self, x, y, font, size, glyphs, x_displacements):
        font_rsc, font_name = self.pdf_page.register_font(font)
        string = ''
        current_string = ''
        char_metrics = font.metrics.glyphs
        for glyph, displ in zip(glyphs, x_displacements):
            displ = (1000 * displ) / size
            try:
                code = font.encoding[glyph]
            except KeyError:
                code = -1
            width = char_metrics[glyph].width
            if code < 0:
                try:
                    differences = font_rsc['Encoding']['Differences']
                except KeyError:
                    occupied_codes = list(font.encoding.values())
                    differences = cos.EncodingDifferences(occupied_codes)
                    font_rsc['Encoding']['Differences'] = differences
                code = differences.register(glyph)
            if code < 32 or code > 127:
                char = '\{:03o}'.format(code)
            else:
                char = chr(code)
                if char in ('\\', '(', ')'):
                    char = '\\' + char
            adjust = int(width - displ)
            if adjust:
                string += '({}{}) {} '.format(current_string, char, adjust)
                current_string = ''
            else:
                current_string += char
        if current_string:
            string += '({})'.format(current_string)

        print('BT', file=self)
        print('/{} {} Tf'.format(font_name, size), file=self)
        print('{} {} Td'.format(x, y), file=self)
        print('[{}] TJ'.format(string), file=self)
        print('ET', file=self)

    def place_image(self, image):
        resources = self.pdf_page.pdf_page['Resources']
        xobjects = resources.setdefault('XObject', cos.Dictionary())
        try:
            image_number = self.pdf_page.pdf_page.image_number
        except AttributeError:
            image_number = 0
        self.pdf_page.pdf_page.image_number = image_number + 1
        xobjects['Im{:03d}'.format(image_number)] = image.xobject
        print('/Im{:03d} Do'.format(image_number), file=self)


class Image(object):
    extensions = ('.pdf', )

    def __init__(self, filename):
        image = PDFReader(filename + self.extensions[0])
        image_page = image.catalog['Pages']['Kids'][0]
        self.width, self.height = image_page['MediaBox'][2:]
        self.xobject = image_page.to_xobject_form()


class PageCanvas(Canvas):
    def __init__(self, page):
        super().__init__(None, 0, 0, page.width, page.height)
        self.parent = page

    @property
    def page(self):
        return self.parent.pyte_page
