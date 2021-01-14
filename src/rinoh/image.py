# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os

from ast import literal_eval
from functools import partial
from pathlib import Path
from token import LPAR, RPAR, NAME, EQUAL, NUMBER, ENDMARKER,  STRING, COMMA

from .attribute import (Attribute, AcceptNoneAttributeType, Integer,
                        OptionSet, AttributesDictionary, ParseError)
from .color import RED
from .dimension import Dimension, PERCENT
from .flowable import (Flowable, FlowableState, HorizontalAlignment,
                       FlowableWidth, StaticGroupedFlowables,
                       GroupedFlowablesStyle, Float, FloatStyle)
from .inline import InlineFlowable
from .layout import ContainerOverflow, EndOfContainer
from .number import NumberedParagraph, NumberedParagraphStyle, format_number
from .paragraph import Paragraph
from .reference import ReferenceType
from .structure import ListOf, ListOfSection
from .text import MixedStyledText, SingleStyledText, TextStyle, StyledText
from .util import posix_path, ReadAliasAttribute, PeekIterator


__all__ = ['Image', 'InlineImage', 'BackgroundImage', 'ImageArgs',
           'Scale', 'Caption', 'CaptionStyle', 'Figure', 'FigureStyle',
           'ListOfFiguresSection', 'ListOfFigures']


class Scale(OptionSet):
    """Scaling factor for images

    Can be a numerical value where a value of 1 keeps the image's original size
    or one of :attr:`values`.

    """

    values = 'fit', 'fill'

    @classmethod
    def check_type(cls, value):
        return super().check_type(value) or value > 0

    @classmethod
    def from_tokens(cls, tokens, source):
        if tokens.next.type == NAME:
            value = super().from_tokens(tokens, source)
        elif tokens.next.type == NUMBER:
            value = float(next(tokens).string)
            if not cls.check_type(value):
                raise ParseError('Scale factor should be larger than 0')
        else:
            raise ParseError('Expecting scale option name or number')
        return value

    @classmethod
    def doc_format(cls):
        return ('{} or a float larger than 0'
                .format(', '.join('``{}``'.format(s)
                                  for s in cls.value_strings)))


class ImageState(FlowableState):
    image = ReadAliasAttribute('flowable')


class Filename(str):
    """str subclass that provides system-independent path comparison"""

    def __eq__(self, other):
        return posix_path(str(self)) == posix_path(str(other))

    def __ne__(self, other):
        return not (self == other)


class RequiredArg(Attribute):
    def __init__(self, accepted_type, description):
        super().__init__(accepted_type, None, description)


class OptionalArg(Attribute):
    pass


class ImagePath(AcceptNoneAttributeType):
    @classmethod
    def from_tokens(cls, tokens, source):
        token = next(tokens)
        if token.type != STRING:
            raise ParseError('Expecting a string')
        return literal_eval(token.string)

    @classmethod
    def doc_format(cls):
        return ('path to an image file enclosed in quotes')


class ImageArgsBase(AttributesDictionary):
    file_or_filename = RequiredArg(ImagePath, 'Path to the image file')

    scale = OptionalArg(Scale, 'fit', 'Scaling factor for the image')
    width = OptionalArg(Dimension, None, 'The width to scale the image to')
    height = OptionalArg(Dimension, None, 'The height to scale the image to')
    dpi = OptionalArg(Integer, 0, 'Overrides the DPI value set in the image')
    rotate = OptionalArg(Integer, 0, 'Angle in degrees to rotate the image')

    @staticmethod
    def _parse_argument(argument_definition, tokens, source):
        arg_tokens = []
        depth = 0
        for token in tokens:
            if token.exact_type == LPAR:
                depth += 1
            elif token.exact_type == RPAR:
                depth -= 1
            arg_tokens.append(token)
            if depth == 0 and tokens.next.exact_type in (COMMA, RPAR,
                                                         ENDMARKER):
                break
        argument_type = argument_definition.accepted_type
        arg_tokens_iter = PeekIterator(arg_tokens)
        argument = argument_type.from_tokens(arg_tokens_iter, source)
        if not arg_tokens_iter.at_end:
            raise ParseError('Syntax error')
        return argument, tokens.next.exact_type in (RPAR, ENDMARKER)

    @classmethod
    def parse_arguments(cls, tokens, source):
        argument_defs = (cls.attribute_definition(name)
                         for name in cls._all_attributes)
        args, kwargs = [], {}

        is_last_arg = False
        # required arguments
        for argument_def in (argdef for argdef in argument_defs
                             if isinstance(argdef, RequiredArg)):
            argument, is_last_arg = cls._parse_argument(argument_def, tokens,
                                                        source)
            args.append(argument)
        # optional arguments
        while not is_last_arg:
            assert next(tokens).exact_type == COMMA
            keyword_token = next(tokens)
            if keyword_token.exact_type != NAME:
                raise ParseError('Expecting a keyword!')
            keyword = keyword_token.string
            equals_token = next(tokens)
            if equals_token.exact_type != EQUAL:
                raise ParseError('Expecting the keyword to be followed by an '
                                 'equals sign.')

            try:
                argument_def = cls.attribute_definition(keyword)
            except KeyError:
                raise ParseError('Unsupported argument keyword: {}'
                                 .format(keyword))
            argument, is_last_arg = cls._parse_argument(argument_def, tokens,
                                                        source)
            kwargs[keyword] = argument
        return args, kwargs


class ImageBase(Flowable):
    """Base class for flowables displaying an image

    If DPI information is embedded in the image, it is used to determine the
    size at which the image is displayed in the document (depending on the
    sizing options specified). Otherwise, a value of 72 DPI is used.

    Args:
        filename_or_file (str, file): the image to display. This can be a path
            to an image file on the file system or a file-like object
            containing the image.
        scale (float): scales the image to `scale` times its original size
        width (Dimension): specifies the absolute width or the width relative
            to the container width
        height (Dimension): specifies the absolute height or the width relative
            to the container **width**.
        dpi (float): overrides the DPI value embedded in the image (or the
            default of 72)
        rotate (float): the angle in degrees to rotate the image over
        limit_width (Dimension): limit the image to this width when none of
            scale, width and height are given and the image would be wider than
            the container

    If only one of `width` or `height` is given, the image is scaled preserving
    the original aspect ratio.

    If `width` or `height` is given, `scale` or `dpi` may not be specified.

    """
    arguments = ImageArgsBase

    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 dpi=None, rotate=0, limit_width=None,
                 id=None, style=None, parent=None, source=None, **kwargs):
        super().__init__(id=id, style=style, parent=parent, source=source,
                         **kwargs)
        self.filename_or_file = filename_or_file
        if (width, height) != (None, None):
            if scale != 1.0:
                raise TypeError('Scale may not be specified when either '
                                'width or height are given.')
            if dpi is not None:
                raise TypeError('DPI may not be specified when either '
                                'width or height are given.')
        self.scale = scale
        self.width = width
        self.height = height
        self.dpi = dpi
        self.rotate = rotate
        self.limit_width = limit_width

    def copy(self, parent=None):
        return type(self)(self.filename_or_file, scale=self.scale,
                          width=self.width, height=self.height, dpi=self.dpi,
                          rotate=self.rotate, limit_width=self.limit_width,
                          id=self.id, style=self.style, parent=parent,
                          source=self.source)

    @property
    def filename(self):
        if isinstance(self.filename_or_file, str):
            return Filename(self.filename_or_file)

    def _short_repr_args(self, flowable_target):
        yield "'{}'".format(self.filename)

    def initial_state(self, container):
         return ImageState(self)

    def _absolute_path_or_file(self):
        try:
            file_path = Path(self.filename_or_file)
        except AttributeError:          # self.filename_or_file is a file
            return self.filename_or_file
        if file_path.is_absolute():
            return file_path
        if self.source_root is None:
            raise ValueError('Image file path should be absolute:'
                             ' {}'.format(file_path))
        return self.source_root / file_path

    def render(self, container, last_descender, state, **kwargs):
        try:
            filename_or_file = self._absolute_path_or_file()
            image = container.document.backend.Image(filename_or_file)
        except OSError as err:
            container.document.error = True
            message = "Error opening image file: {}".format(err)
            self.warn(message)
            text = SingleStyledText(message, style=TextStyle(font_color=RED))
            return Paragraph(text).flow(container, last_descender)
        left, top = 0, float(container.cursor)
        width = self._width(container)
        try:
            scale_width = width.to_points(container.width) / image.width
        except AttributeError:  # width is a FlowableWidth
            scale_width = None
        if self.height is not None:
            scale_height = self.height.to_points(container.width) / image.height
            if scale_width is None:
                scale_width = scale_height
        else:
            scale_height = scale_width
        if scale_width is None:                   # no width or height given
            if self.scale in Scale.values:
                w_scale = float(container.width) / image.width
                h_scale = float(container.remaining_height) / image.height
                min_or_max = min if self.scale == Scale.FIT else max
                scale_width = scale_height = min_or_max(w_scale, h_scale)
            else:
                scale_width = scale_height = self.scale
        dpi_x, dpi_y = image.dpi
        dpi_scale_x = (dpi_x / self.dpi) if self.dpi and dpi_x else 1
        dpi_scale_y = (dpi_y / self.dpi) if self.dpi and dpi_y else 1
        if (scale_width == scale_height == 1.0    # limit width if necessary
                and self.limit_width is not None
                and image.width * dpi_scale_x > container.width):
            limit_width = self.limit_width.to_points(container.width)
            scale_width = scale_height = limit_width / image.width
        w, h = container.canvas.place_image(image, left, top,
                                            container.document,
                                            scale_width * dpi_scale_x,
                                            scale_height * dpi_scale_y,
                                            self.rotate)
        ignore_overflow = (self.scale == Scale.FIT) or container.page._empty
        try:
            container.advance(h, ignore_overflow)
        except ContainerOverflow:
            raise EndOfContainer(state)
        return w, h, 0


class InlineImageArgs(ImageArgsBase):
    baseline = OptionalArg(Dimension, 0, "Location of this inline image's "
                                         "baseline")


class InlineImage(ImageBase, InlineFlowable):
    directive = 'image'
    arguments = InlineImageArgs

    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 dpi=None, rotate=0, baseline=None,
                 id=None, style=None, parent=None, source=None):
        super().__init__(filename_or_file=filename_or_file, scale=scale,
                         height=height, dpi=dpi, rotate=rotate,
                         baseline=baseline, id=id, style=style, parent=parent,
                         source=source)
        self.width = width

    def _width(self, container):
        return FlowableWidth.AUTO if self.width is None else self.width

    def copy(self, parent=None):
        return type(self)(self.filename_or_file, scale=self.scale,
                          width=self.width, height=self.height, dpi=self.dpi,
                          rotate=self.rotate, baseline=self.baseline,
                          id=self.id, style=self.style, parent=parent,
                          source=self.source)


class _Image(ImageBase):
    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 dpi=None, rotate=0, limit_width=100*PERCENT, align=None,
                 id=None, style=None, parent=None, source=None):
        super().__init__(filename_or_file=filename_or_file, scale=scale,
                         width=width, height=height, dpi=dpi, rotate=rotate,
                         limit_width=limit_width, align=align,
                         id=id, style=style, parent=parent, source=source)


class Image(_Image):
    pass


class BackgroundImageMeta(type(_Image), type(AttributesDictionary)):
    pass


class ImageArgs(ImageArgsBase):
    limit_width = Attribute(Dimension, 100*PERCENT, 'Limit the image width '
                            'when none of :attr:`scale`, :attr:`width` and '
                            ':attr:`height` are given and the image would '
                            'be wider than the container')
    align = Attribute(HorizontalAlignment, 'left', 'How to align the image '
                                                   'within the page')


class BackgroundImage(_Image, AcceptNoneAttributeType):
    """Image to place in the background of a page

    Takes the same arguments as :class:`Image`.

    """
    arguments = ImageArgs

    @classmethod
    def from_tokens(cls, tokens, source):
        args, kwargs = cls.arguments.parse_arguments(tokens, source)
        return cls(*args, source=source, **kwargs)

    @classmethod
    def doc_format(cls):
        return ('filename of an image file enclosed in quotes, optionally '
                'followed by space-delimited keyword arguments '
                '(``<keyword>=<value>``) that determine how the image is '
                'displayed')


class CaptionStyle(NumberedParagraphStyle):
    numbering_level = Attribute(Integer, 1, 'At which section level to '
                                            'restart numbering')
    number_separator = Attribute(StyledText, '.', 'Characters inserted between'
                                 ' the section number and the caption number')


class Caption(NumberedParagraph):
    style_class = CaptionStyle

    @property
    def referenceable(self):
        return self.parent

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        document = flowable_target.document
        get_style = partial(self.get_style, container=flowable_target)
        category = self.referenceable.category
        numbering_level = get_style('numbering_level')
        section = self.section
        while section and section.level > numbering_level:
            section = section.parent.section
        section_id = section.get_id(document, False) if section else None
        category_counters = document.counters.setdefault(category, {})
        category_counter = category_counters.setdefault(section_id, [])
        category_counter.append(self)
        number_format = get_style('number_format')
        number = format_number(len(category_counter), number_format)
        if section_id:
            section_number = document.get_reference(section_id, 'number')
            sep = get_style('number_separator') or SingleStyledText('')
            number = section_number + sep.to_string(flowable_target) + number
        reference = '{} {}'.format(category, number)
        for id in self.referenceable.get_ids(document):
            document.set_reference(id, ReferenceType.NUMBER, number)
            document.set_reference(id, ReferenceType.REFERENCE, reference)
            document.set_reference(id, ReferenceType.TITLE,
                                   self.content.to_string(None))

    def text(self, container):
        label = self.referenceable.category + ' ' + self.number(container)
        return MixedStyledText(label + self.content, parent=self)


class FigureStyle(FloatStyle, GroupedFlowablesStyle):
    pass


class Figure(Float, StaticGroupedFlowables):
    style_class = FigureStyle
    category = 'Figure'


class ListOfFigures(ListOf):
    category = 'Figure'


class ListOfFiguresSection(ListOfSection):
    list_class = ListOfFigures
