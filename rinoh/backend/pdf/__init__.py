# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import math

from io import StringIO, BytesIO
from contextlib import contextmanager

from . import cos
from .reader import PDFReader, PDFPageReader
from .filter import FlateDecode
from .xobject.jpeg import JPEGReader
from .xobject.png import PNGReader

from ...font.type1 import Type1Font
from ...font.opentype import OpenTypeFont


class Document(object):
    extension = '.pdf'

    def __init__(self, rinoh_document, creator):
        self.rinoh_document = rinoh_document
        self.cos_document = cos.Document(creator)
        self.pages = []
        self.fonts = {}
        self._font_number = 0
        self._image_number = 0

    def get_unique_font_number(self):
        self._font_number += 1
        return self._font_number

    def get_unique_image_number(self):
        self._image_number += 1
        return self._image_number

    def get_metadata(self, field):
        return str(self.cos_document.info[field.capitalize()])

    def set_metadata(self, field, value):
        self.cos_document.set_info(field.capitalize(), value)

    def register_font(self, font):
        try:
            font_number, font_rsc = self.fonts[font]
        except KeyError:
            if isinstance(font, Type1Font):
                font_file = cos.Type1FontFile(font.font_program.header,
                                              font.font_program.body,
                                              filter=FlateDecode())
            elif isinstance(font, OpenTypeFont):
                ff_cls = (cos.OpenTypeFontFile if 'CFF' in font
                          else cos.TrueTypeFontFile)
                with open(font.filename, 'rb') as font_data:
                    font_file = ff_cls(font_data.read(), filter=FlateDecode())
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
                cf_cls = cos.CIDFontType0 if 'CFF' in font else cos.CIDFontType2
                cid_font = cf_cls(font.name, cid_system_info, font_desc, w=w)
                mapping = font['cmap'][(3, 1)].mapping
                to_unicode = cos.ToUnicode(mapping, filter=FlateDecode())
                font_rsc = cos.CompositeFont(cid_font, 'Identity-H', to_unicode)
            font_number = self.get_unique_font_number()
            self.fonts[font] = font_number, font_rsc
        return font_number, font_rsc

    def write(self, file):
        for page in self.pages:
            contents = cos.Stream(filter=FlateDecode())
            contents.write(page.canvas.getvalue().encode('utf_8'))
            page.cos_page['Contents'] = contents
        self.cos_document.write(file)


class Page(object):
    def __init__(self, rinoh_page, document, width, height):
        self.rinoh_page = rinoh_page
        cos_pages = document.cos_document.catalog['Pages']
        self.cos_page = cos_pages.new_page(float(width), float(height))
        self.width = width
        self.height = height
        self.canvas = PageCanvas(self)
        document.pages.append(self)

    @property
    def document_part(self):
        return self.rinoh_page.document_part

    @property
    def document(self):
        return self.rinoh_page.document

    def add_font_resource(self, font_name, font_rsc):
        page_rsc = self.cos_page['Resources']
        fonts_dict = page_rsc.setdefault('Font', cos.Dictionary())
        fonts_dict[font_name] = font_rsc


class Canvas(StringIO):
    def __init__(self, parent, clip=False):
        super().__init__()
        self.parent = parent
        self.fonts = {}
        self.images = {}
        self.annotations = []
        self.destinations = []
        self.offset = None

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
        self.offset = left, top
        with self.parent.save_state():
            self.parent.translate(left, top)
            self.parent.write(self.getvalue())
        self.propagate(self.fonts, self.images, self.annotations)

    def propagate(self, fonts, images, annotations):
        if self.offset:
            left, top = self.offset
            for annotation_placement in annotations:
                annotation_placement.translate(left, top)
            self.parent.propagate(fonts, images, annotations)
        else:
            self.fonts.update(fonts)
            self.images.update(images)
            self.annotations += annotations

    @contextmanager
    def save_state(self):
        print('q', file=self)
        yield
        print('Q', file=self)

    def translate(self, x, y):
        print('1 0 0 1 {:f} {:f} cm'.format(x, - y), file=self)

    def rotate(self, degrees):
        rad = math.radians(degrees)
        sine, cosine = math.sin(rad), math.cos(rad)
        print('{cos:f} {sin:f} {neg_sin:f} {cos:f} 0 0 cm'
              .format(cos=cosine, sin=sine, neg_sin=-sine,), file=self)

    def scale(self, x, y=None):
        if y is None:
            y = x
        print('{:f} 0 0 {:f} 0 0 cm'.format(x, y), file=self)

    def move_to(self, x, y):
        print('{:f} {:f} m'.format(x, y), file=self)

    def line_to(self, x, y):
        print('{:f} {:f} l'.format(x, y), file=self)

    def new_path(self):
        pass

    def close_path(self):
        print('h', file=self)

    def line_path(self, points):
        self.new_path()
        self.move_to(*points[0])
        for point in points[1:]:
            self.line_to(*point)

    def line_width(self, width):
        print('{0} w'.format(float(width)), file=self)

    def stroke_color(self, color):
        r, g, b, a = color.rgba
        print('{0} {1} {2} RG'.format(r, g, b), file=self)

    def fill_color(self, color):
        r, g, b, a = color.rgba
        print('{0} {1} {2} rg'.format(r, g, b), file=self)

    def stroke(self, line_width=None, color=None):
        with self.save_state():
            if color:
                self.stroke_color(color)
            if line_width:
                self.line_width(line_width)
            print('s', file=self)

    def fill(self, color=None):
        with self.save_state():
            if color:
                self.fill_color(color)
            print('f', file=self)

    def stroke_and_fill(self, stroke_width, stroke_color, fill_color):
        with self.save_state():
            self.line_width(stroke_width)
            self.stroke_color(stroke_color)
            self.fill_color(fill_color)
            print('B', file=self)

    def register_font(self, document, font):
        font_number, font_rsc = document.backend_document.register_font(font)
        font_name = 'F{}'.format(font_number)
        self.fonts.setdefault(font_name, font_rsc)
        return font_name, font_rsc

    def show_glyphs(self, left, cursor, span, glyph_and_widths, document):
        font = span.font(document)
        size = span.height(document)
        color = span.get_style('font_color', document)
        font_name, font_rsc = self.register_font(document, font)
        string = ''
        current_string = ''
        total_width = 0
        for glyph_and_width in glyph_and_widths:
            glyph, width = glyph_and_width.glyph, glyph_and_width.width
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
        with self.save_state():
            print('BT', file=self)
            print('/{} {} Tf'.format(font_name, size), file=self)
            self.fill_color(color)
            print('{:f} {:f} Td'.format(left, - (cursor - span.y_offset(document))),
                  file=self)
            print('[{}] TJ'.format(string), file=self)
            print('ET', file=self)
        return total_width

    def annotate(self, annotation, left, top, width, height):
        ann_loc = AnnotationLocation(annotation, left, top, width, height)
        self.annotations.append(ann_loc)

    def place_image(self, image, left, top, document, scale=1.0, width=None,
                    rotate=0):
        image_number = document.backend_document.get_unique_image_number()
        self.images[image_number] = image
        rad = math.radians(rotate)
        sine, cosine = abs(math.sin(rad)), abs(math.cos(rad))
        im_width = image.width * cosine + image.height * sine
        im_height = image.width * sine + image.height * cosine
        if width is not None:
            assert scale is None
            scale = width / im_width
        with self.save_state():
            self.translate(left, top)
            self.translate(scale * im_width / 2, scale * im_height / 2)
            self.rotate(rotate)
            self.translate(- scale * image.width / 2, scale * image.height / 2)
            self.scale(scale)
            if image.xobject.subtype == 'Image':
                self.scale(image.width, image.height)
            print('/Im{} Do'.format(image_number), file=self)
        return im_width * scale, im_height * scale


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

    def propagate(self, fonts, images, annotations):
        # fonts
        for font_name, font_rsc in fonts.items():
            self._backend_page.add_font_resource(font_name, font_rsc)

        # images
        resources = self.cos_page.cos_page['Resources']
        for image_number, image in images.items():
            xobjects = resources.setdefault('XObject', cos.Dictionary())
            xobjects['Im{}'.format(image_number)] = image.xobject

        # annotations
        page_height = float(self._backend_page.height)
        cos_document = self.page.document.backend_document.cos_document
        cos_page = self.cos_page.cos_page
        names = cos_document.catalog.setdefault('Names', cos.Dictionary(True))
        dests = names.setdefault('Dests', cos.Dictionary(True))
        # TODO: dest_names should be sorted by name
        dests_names = dests.setdefault('Names', cos.Array())
        annots = cos_page.setdefault('Annots', cos.Array())
        for annotation_location in annotations:
            annotation = annotation_location.annotation
            left = annotation_location.left
            top = page_height - annotation_location.top
            if annotation.type == 'NamedDestination':
                dest = cos.Array([cos_page, cos.Name('XYZ'),
                                  cos.Real(left), cos.Real(top), cos.Real(0)],
                                 indirect=True)
                key = cos.String(annotation.name)
                if key not in dests_names:  # avoid dupes
                    dests_names.append(key)
                    dests_names.append(dest)
                continue
            right = left + annotation_location.width
            bottom = top - annotation_location.height
            rect = cos.Rectangle(left, bottom, right, top)
            if annotation.type == 'URI':
                a = cos.URIAction(annotation.target)
                annot = cos.LinkAnnotation(rect, action=a)
            elif annotation.type == 'NamedDestinationLink':
                name = cos.String(annotation.name)
                annot = cos.LinkAnnotation(rect, destination=name)
            else:
                raise NotImplementedError
            annots.append(annot)


class AnnotationLocation(object):
    def __init__(self, annotation, left, top, width, height):
        self.annotation = annotation
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def translate(self, offset_left, offset_top):
        self.left += offset_left
        self.top += offset_top


class Image(object):
    def __init__(self, filename_or_file):
        for Reader in (PDFPageReader, PNGReader, JPEGReader):
            try:
                self.xobject = Reader(filename_or_file)
                break
            except ValueError:
                pass
        else:
            png_file = self._convert_to_png(filename_or_file)
            self.xobject = PNGReader(png_file)

    @property
    def width(self):
        return self.xobject.width

    @property
    def height(self):
        return self.xobject.height

    def _convert_to_png(self, filename_or_file):
        import PIL
        png_image = BytesIO()
        input_image = PIL.Image.open(filename_or_file)
        metadata = {}
        if 'dpi' in input_image.info and 0 not in input_image.info['dpi']:
            metadata['dpi'] = input_image.info['dpi']
        input_image.save(png_image, 'PNG', **metadata)
        png_image.seek(0)
        return png_image


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
