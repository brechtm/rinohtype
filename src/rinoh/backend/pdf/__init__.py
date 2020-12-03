# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import math

from io import BytesIO
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

    def __init__(self, creator,
                 title=None, author=None, subject=None, keywords=None):
        self.cos_document = cos.Document(creator, title, author, subject,
                                         keywords)
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
            symbolic = True
            if isinstance(font, Type1Font):
                font_file = (None if font.core else
                             cos.Type1FontFile(font.font_program.header,
                                               font.font_program.body,
                                               filter=FlateDecode()))
                if font.encoding_scheme == 'AdobeStandardEncoding':
                    symbolic = False
            elif isinstance(font, OpenTypeFont):
                ff_cls = (cos.OpenTypeFontFile if 'CFF' in font
                          else cos.TrueTypeFontFile)
                with open(font.filename, 'rb') as font_data:
                    font_file = ff_cls(font_data.read(), filter=FlateDecode())
            # TODO: properly determine flags
            font_desc = cos.FontDescriptor(font, symbolic, font_file)
            if isinstance(font, Type1Font):
                font_rsc = cos.Type1Font(font, font_desc)
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

    def create_outlines(self, sections_tree):
        outlines = self.cos_document.catalog['Outlines'] = cos.Outlines()
        self._create_outline_level(sections_tree, outlines, True)

    def _create_outline_level(self, sections_tree, parent, top_level):
        count = 0
        for count, section_item in enumerate(sections_tree, start=1):
            (section_id, section_number,
             section_title, subsections_tree) = section_item
            if section_number:
                section_label = section_number + ' ' + section_title
            else:
                section_label = section_title
            current = cos.OutlineEntry(section_label, section_id, parent)
            if subsections_tree:
                self._create_outline_level(subsections_tree, current, False)
            if count == 1:
                parent['First'] = current
            else:
                previous['Next'] = current
                current['Prev'] = previous
            previous = current
        if count:
            parent['Last'] = current
        parent['Count'] = cos.Integer(count if top_level else - count)

    def write(self, file):
        page_labels = self.cos_document.catalog['PageLabels']['Nums']
        last_number_format = None
        for index, page in enumerate(self.pages):
            contents = cos.Stream(filter=FlateDecode())
            contents.write(page.canvas.getvalue())
            page.cos_page['Contents'] = contents
            if page.number_format != last_number_format:
                pdf_number_format = PAGE_NUMBER_FORMATS[page.number_format]
                page_labels.append(cos.Integer(index))
                page_labels.append(cos.PageLabel(pdf_number_format,
                                                 start=page.number))
                last_number_format = page.number_format
        self.cos_document.write(file)


PAGE_NUMBER_FORMATS = {'number': cos.DECIMAL_ARABIC,
                       'lowercase characters': cos.LOWERCASE_LETTERS,
                       'uppercase characters': cos.UPPERCASE_LETTERS,
                       'lowercase roman': cos.LOWERCASE_ROMAN,
                       'uppercase roman': cos.UPPERCASE_ROMAN}


class Page(object):
    def __init__(self, backend_document, width, height, number, number_format):
        self.backend_document = backend_document
        cos_pages = backend_document.cos_document.catalog['Pages']
        self.cos_page = cos_pages.new_page(float(width), float(height))
        self.width = width
        self.height = height
        self.number = number
        self.number_format = number_format
        self.canvas = PageCanvas(self)
        self.backend_document.pages.append(self)

    def add_font_resource(self, font_name, font_rsc):
        page_rsc = self.cos_page['Resources']
        fonts_dict = page_rsc.setdefault('Font', cos.Dictionary())
        fonts_dict[font_name] = font_rsc


class Canvas(BytesIO):
    def __init__(self, clip=False):
        super().__init__()
        self.fonts = {}
        self.images = {}
        self.annotations = []

    def append(self, parent_canvas, left, top):
        with parent_canvas.save_state():
            parent_canvas.translate(left, top)
            parent_canvas.write(self.getvalue())
        self.propagate_annotations(parent_canvas, left, top)

    def propagate_annotations(self, parent_canvas, left, top):
        translated_annotations = (annotation_location + (left, top)
                                  for annotation_location in self.annotations)
        parent_canvas.fonts.update(self.fonts)
        parent_canvas.images.update(self.images)
        parent_canvas.annotations.extend(translated_annotations)

    def print(self, string):
        self.write(string.encode('ascii') + b'\n')

    @contextmanager
    def save_state(self):
        self.print('q')
        yield
        self.print('Q')

    def translate(self, x, y):
        self.print('1 0 0 1 {:f} {:f} cm'.format(x, - y))

    def rotate(self, degrees):
        rad = math.radians(degrees)
        sine, cosine = math.sin(rad), math.cos(rad)
        self.print('{cos:f} {sin:f} {neg_sin:f} {cos:f} 0 0 cm'
                   .format(cos=cosine, sin=sine, neg_sin=-sine))

    def scale(self, x, y=None):
        if y is None:
            y = x
        self.print('{:f} 0 0 {:f} 0 0 cm'.format(x, y))

    def move_to(self, x, y):
        self.print('{:f} {:f} m'.format(x, y))

    def line_to(self, x, y):
        self.print('{:f} {:f} l'.format(x, y))

    def new_path(self):
        pass

    def close_path(self):
        self.print('h')

    def line_path(self, points):
        self.new_path()
        self.move_to(*points[0])
        for point in points[1:]:
            self.line_to(*point)

    def line_width(self, width):
        self.print('{0} w'.format(float(width)))

    def stroke_color(self, color):
        r, g, b, a = color.rgba
        self.print('{0} {1} {2} RG'.format(r, g, b))

    def fill_color(self, color):
        r, g, b, a = color.rgba
        self.print('{0} {1} {2} rg'.format(r, g, b))

    def stroke(self, line_width=None, color=None):
        if color:
            self.stroke_color(color)
        if line_width:
            self.line_width(line_width)
        self.print('S')

    def fill(self, color=None):
        with self.save_state():
            if color:
                self.fill_color(color)
                self.print('f')

    def stroke_and_fill(self, stroke_width, stroke_color, fill_color):
        with self.save_state():
            self.line_width(stroke_width)
            self.stroke_color(stroke_color)
            self.fill_color(fill_color)
            self.print('B')

    def register_font(self, document, font):
        font_number, font_rsc = document.backend_document.register_font(font)
        font_name = 'F{}'.format(font_number)
        self.fonts.setdefault(font_name, font_rsc)
        return font_name, font_rsc

    def show_glyphs(self, left, cursor, span, glyph_and_widths, container):
        font = span.font(container)
        size = span.height(container)
        color = span.get_style('font_color', container)
        font_name, font_rsc = self.register_font(container.document, font)
        string = ''
        current_string = ''
        total_width = 0
        for glyph_and_width in glyph_and_widths:
            glyph, width = glyph_and_width.glyph, glyph_and_width.width
            total_width += width
            displ = (1000 * width) / size
            if font.encoding:
                code = font_rsc.get_code(glyph)
                char = CODE_TO_CHAR[code]
            else:
                code = glyph.code
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
            self.print('BT')
            self.print('/{} {} Tf'.format(font_name, size))
            self.fill_color(color)
            y_offset = span.y_offset(container)
            self.print('{:f} {:f} Td'.format(left, - (cursor - y_offset)))
            self.print('[{}] TJ'.format(string))
            self.print('ET')
        return total_width

    def annotate(self, annotation, left, top, width, height):
        ann_loc = AnnotationLocation(annotation, left, top, width, height)
        self.annotations.append(ann_loc)

    def place_image(self, image, left, top, document,
                    scale_width=1, scale_height=1, rotate=0):
        image_number = document.backend_document.get_unique_image_number()
        self.images[image_number] = image
        rad = math.radians(rotate)
        sine, cosine = abs(math.sin(rad)), abs(math.cos(rad))
        im_width = image.width * cosine + image.height * sine
        im_height = image.width * sine + image.height * cosine
        scaled_width = scale_width * im_width
        scaled_height = scale_height * im_height
        with self.save_state():
            self.translate(left, top)
            self.translate(scaled_width / 2, scaled_height / 2)
            self.rotate(rotate)
            self.translate(- scale_width * image.width / 2,
                           scale_height * image.height / 2)
            self.scale(scale_width, scale_height)
            if image.xobject.subtype == 'Image':
                self.scale(image.width, image.height)
            self.print('/Im{} Do'.format(image_number))
        return scaled_width, scaled_height


class PageCanvas(Canvas):
    def __init__(self, backend_page):
        super().__init__(None)
        self.backend_page = backend_page
        self.translate(0, - float(backend_page.height))

    def place_annotations(self):
        # fonts
        for font_name, font_rsc in self.fonts.items():
            self.backend_page.add_font_resource(font_name, font_rsc)

        # images
        resources = self.backend_page.cos_page['Resources']
        for image_number, image in self.images.items():
            xobjects = resources.setdefault('XObject', cos.Dictionary())
            xobjects['Im{}'.format(image_number)] = image.xobject

        # annotations
        page_height = float(self.backend_page.height)
        cos_document = self.backend_page.backend_document.cos_document
        cos_page = self.backend_page.cos_page
        annots = cos_page.setdefault('Annots', cos.Array())
        for annotation_location in self.annotations:
            annotation = annotation_location.annotation
            left = annotation_location.left
            top = page_height - annotation_location.top
            if annotation.type == 'NamedDestination':
                dest = cos.Array([cos_page, cos.Name('XYZ'),
                                  cos.Real(left), cos.Real(top),
                                  cos.Real(0)], indirect=True)
                for name in annotation.names:
                    key = cos.String(name)
                    if key not in cos_document.dests:
                        cos_document.dests[key] = dest
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

    def __add__(self, offset):
        offset_left, offset_top = offset
        return self.__class__(self.annotation, self.left + offset_left,
                              self.top + offset_top, self.width, self.height)


class Image(object):
    def __init__(self, filename_or_file):
        try:
            file_position = filename_or_file.tell()
        except AttributeError:
            file_position = None
        for Reader in (PDFPageReader, PNGReader, JPEGReader):
            try:
                self.xobject = Reader(filename_or_file)
                break
            except ValueError:
                pass
            finally:
                if file_position is not None:
                    filename_or_file.seek(file_position)
        else:
            png_file = self._convert_to_png(filename_or_file)
            self.xobject = PNGReader(png_file)

    @property
    def width(self):
        return self.xobject.width

    @property
    def height(self):
        return self.xobject.height

    @property
    def dpi(self):
        return self.xobject.dpi

    def _convert_to_png(self, filename_or_file):
        from PIL import Image as PILImage
        png_image = BytesIO()
        input_image = PILImage.open(filename_or_file)
        metadata = {}
        if 'dpi' in input_image.info and 0 not in input_image.info['dpi']:
            metadata['dpi'] = input_image.info['dpi']
        input_image.save(png_image, 'PNG', **metadata)
        png_image.seek(0)
        return png_image


CODE_TO_CHAR = {}


def _code_to_char(code):
    if code < 32 or code > 127:
        char = r'\{:03o}'.format(code)
    else:
        char = chr(code)
        if char in r'\()':
            char = '\\' + char
    return char


for code in range(256):
    CODE_TO_CHAR[code] = _code_to_char(code)
