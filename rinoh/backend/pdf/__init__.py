# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from io import StringIO
from . import cos

from .reader import PDFReader
from .filter import FlateDecode
from ...font.type1 import Type1Font
from ...font.opentype import OpenTypeFont


try:
    profile
except NameError:
    def profile(function):
        return function


class Document(object):
    extension = '.pdf'

    def __init__(self, rinoh_document, title):
        self.rinoh_document = rinoh_document
        self.cos_document = cos.Document()
        self.pages = []
        self.fonts = {}

    def register_font(self, font):
        try:
            font_rsc = self.fonts[font]
        except KeyError:
            if isinstance(font, Type1Font):
                font_file = cos.Type1FontFile(font.font_program.header,
                                              font.font_program.body,
                                              filter=FlateDecode())
            elif isinstance(font, OpenTypeFont):
                with open(font.filename, 'rb') as font_data:
                    font_file = cos.OpenTypeFontFile(font_data.read(),
                                                     filter=FlateDecode())
            font_desc = cos.FontDescriptor(font.name,
                                           4, # TODO: properly determine flags
                                           font.bounding_box,
                                           font.italic_angle,
                                           font.ascender,
                                           font.descender,
                                           font.cap_height,
                                           font.stem_v,
                                           font_file,
                                           font.x_height)
            if isinstance(font, Type1Font):
                font_rsc = cos.Type1Font(font, cos.FontEncoding(), font_desc)
            elif isinstance(font, OpenTypeFont):
                cid_system_info = cos.CIDSystemInfo('Identity', 'Adobe', 0)
                widths = font['hmtx']['advanceWidth']
                w = cos.Array([cos.Integer(0),
                               cos.Array(map(cos.Integer, widths))])
                if 'CFF' in font:
                    cid_font = cos.CIDFontType0(font.name, cid_system_info,
                                                font_desc, w=w)
                else:
                    cid_font = cos.CIDFontType2(font.name, cid_system_info,
                                                font_desc, w=w)
                mapping = font['cmap'][(3, 1)].mapping
                to_unicode = cos.ToUnicode(mapping, filter=FlateDecode())
                font_rsc = cos.CompositeFont(cid_font, 'Identity-H', to_unicode)
            self.fonts[font] = font_rsc
        return font_rsc

    def write(self, filename):
        for page in self.pages:
            contents = cos.Stream(filter=FlateDecode())
            contents.write(page.canvas.getvalue().encode('utf_8'))
            page.cos_page['Contents'] = contents
        file = open(filename + self.extension, 'wb')
        self.cos_document.write(file)
        file.close()


class Page(object):
    def __init__(self, rinoh_page, document, width, height):
        self.rinoh_page = rinoh_page
        cos_pages = document.cos_document.catalog['Pages']
        self.cos_page = cos_pages.new_page(float(width), float(height))
        self.width = width
        self.height = height
        self.canvas = PageCanvas(self)
        document.pages.append(self)
        self.font_number = 1
        self.font_names = {}

    @property
    def document(self):
        return self.rinoh_page.document

    def register_font(self, font):
        try:
            font_rsc, name = self.font_names[font]
        except KeyError:
            font_rsc = self.document.backend_document.register_font(font)
            name = 'F{}'.format(self.font_number)
            self.font_number += 1
            page_rsc = self.cos_page['Resources']
            fonts_dict = page_rsc.setdefault('Font', cos.Dictionary())
            fonts_dict[name] = font_rsc
            self.font_names[font] = font_rsc, name
        return font_rsc, name


class Canvas(StringIO):
    def __init__(self, parent, clip=False):
        super().__init__()
        self.parent = parent

    @property
    def page(self):
        return self.parent.page

    @property
    def cos_page(self):
        return self.page.backend_page

    @property
    def document(self):
        return self.page.document

    def new(self, clip=False):
        return Canvas(self, clip)

    def append(self, left, top):
        self.parent.save_state()
        self.parent.translate(left, top)
        self.parent.write(self.getvalue())
        self.parent.restore_state()

    def save_state(self):
        print('q', file=self)

    def restore_state(self):
        print('Q', file=self)

    def translate(self, x, y):
        print('1 0 0 1 {} {} cm'.format(x, - y), file=self)

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

    @profile
    def show_glyphs(self, left, cursor, glyph_span):
        span = glyph_span.span
        font = span.font
        size = span.height
        font_rsc, font_name = self.cos_page.register_font(font)
        string = ''
        current_string = ''
        total_width = 0
        for glyph, width in glyph_span:
            total_width += width
            displ = (1000 * width) / size
            code = glyph.code
            if font.encoding:
                if code < 0:
                    try:
                        differences = font_rsc['Encoding']['Differences']
                    except KeyError:
                        occupied = list(font.encoding.values())
                        differences = cos.EncodingDifferences(occupied)
                        font_rsc['Encoding']['Differences'] = differences
                    code = differences.register(glyph)
                char = CODE_TO_CHAR[code]
            else:
                high, low = code >> 8, code & 0xFF
                char = CODE_TO_CHAR[high] + CODE_TO_CHAR[low]
            adjust = int(glyph.width - displ)
            if adjust:
                string += '({}{}) {} '.format(current_string, char,
                                              adjust)
                current_string = ''
            else:
                current_string += char
        if current_string:
            string += '({})'.format(current_string)
        print('BT', file=self)
        print('/{} {} Tf'.format(font_name, size), file=self)
        print('{} {} Td'.format(left, - (cursor - span.y_offset)), file=self)
        print('[{}] TJ'.format(string), file=self)
        print('ET', file=self)
        return total_width

    def place_image(self, image, left, top, scale=1.0):
        resources = self.cos_page.cos_page['Resources']
        xobjects = resources.setdefault('XObject', cos.Dictionary())
        try:
            image_number = self.cos_page.cos_page.image_number
        except AttributeError:
            image_number = 0
        self.cos_page.cos_page.image_number = image_number + 1
        xobjects['Im{:03d}'.format(image_number)] = image.xobject
        self.save_state()
        self.translate(left, top + image.height)
        self.scale(scale)
        print('/Im{:03d} Do'.format(image_number), file=self)
        self.restore_state()


class Image(object):
    extensions = ('.pdf', )

    def __init__(self, filename):
        image = PDFReader(filename + self.extensions[0])
        image_page = image.catalog['Pages']['Kids'][0]
        self.width, self.height = image_page['MediaBox'][2:]
        self.xobject = image_page.to_xobject_form()


class PageCanvas(Canvas):
    def __init__(self, backend_page):
        super().__init__(None)
        self._backend_page = backend_page
        self.translate(0, - float(backend_page.height))

    @property
    def page(self):
        return self._backend_page.rinoh_page

    def append(self, left, top):
        pass


CODE_TO_CHAR = {}


def _code_to_char(code):
    if code < 32 or code > 127:
        char = '\{:03o}'.format(code)
    else:
        char = chr(code)
        if char in ('\\', '(', ')'):
            char = '\\' + char
    return char


for code in range(256):
    CODE_TO_CHAR[code] = _code_to_char(code)
