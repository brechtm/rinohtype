# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import os

from .attribute import AttributeType
from .color import RED
from .flowable import (Flowable, InseparableFlowables, StaticGroupedFlowables,
                       HorizontallyAlignedFlowable,
                       HorizontallyAlignedFlowableState, Float, FloatStyle,
                       GroupedFlowablesStyle)
from .inline import InlineFlowable
from .layout import ContainerOverflow, EndOfContainer
from .number import NumberedParagraph
from .paragraph import Paragraph
from .reference import NUMBER
from .text import MixedStyledText, SingleStyledText, TextStyle
from .util import ReadAliasAttribute


__all__ = ['InlineImage', 'Image', 'Caption', 'Figure']


LEFT = 'left'
CENTER = 'center'
RIGHT = 'right'

FIT = 'fit'
FILL = 'fill'


class ImageState(HorizontallyAlignedFlowableState):
    image = ReadAliasAttribute('flowable')
    width = None


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
        width (DimensionBase, Fraction): specifies the absolute width
            (DimensionBase) or the width relative to the container width
            (Fraction).
        height (DimensionBase): specifies the absolute height (DimensionBase)
            or the width relative to the container **width** (Fraction).
        dpi (float): overrides the DPI value embedded in the image (or the
            default of 72)
        rotate (float): the angle in degrees to rotate the image over
        limit_width (DimensionBase, Fraction): limit the image to this width
            when none of scale, width and height are given and the image would
            be wider than the container.

    If only one of `width` or `height` is given, the image is scaled preserving
    the original aspect ratio.

    If `width` or `height` is given, `scale` or `dpi` may not be specified.

    """

    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 dpi=None, rotate=0, limit_width=None,
                 id=None, style=None, parent=None, **kwargs):
        super().__init__(id=id, style=style, parent=parent, **kwargs)
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

    @property
    def filename(self):
        if isinstance(self.filename_or_file, str):
            return self.filename_or_file

    def _short_repr_args(self, flowable_target):
        yield "'{}'".format(self.filename)

    def initial_state(self, container):
         return ImageState(self)

    def render(self, container, last_descender, state, **kwargs):
        try:
            try:
                source_root = container.document.document_tree.source_root
                filename_or_file = os.path.join(source_root,
                                                self.filename_or_file)
            except AttributeError:  # self.filename_or_file is a file
                filename_or_file = self.filename_or_file
            image = container.document.backend.Image(filename_or_file)
        except OSError as err:
            message = "Error opening image file: {}".format(err)
            self.warn(message)
            text = SingleStyledText(message, style=TextStyle(font_color=RED))
            return Paragraph(text).flow(container, last_descender)
        left, top = 0, float(container.cursor)
        width = self._width(container)
        if width is not None:
            scale_width = width.to_points(container.width) / image.width
        else:
            scale_width = None
        if self.height is not None:
            scale_height = self.height.to_points(container.width) / image.height
            if scale_width is None:
                scale_width = scale_height
        else:
            scale_height = scale_width
        if scale_width is None:                   # no width or height given
            if self.scale in (FIT, FILL):
                w_scale = float(container.width) / image.width
                h_scale = float(container.remaining_height) / image.height
                min_or_max = min if self.scale == FIT else max
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
        ignore_overflow = (self.scale == FIT) or container.page._empty
        try:
            container.advance(h, ignore_overflow)
        except ContainerOverflow:
            raise EndOfContainer(state)
        return w, h, 0


class InlineImage(ImageBase, InlineFlowable):
    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 dpi=None, rotate=0, baseline=None,
                 id=None, style=None, parent=None):
        super().__init__(filename_or_file=filename_or_file, scale=scale,
                         height=height, dpi=dpi, rotate=rotate,
                         baseline=baseline, id=id, style=style, parent=parent)
        self.width = width

    def _width(self, container):
        return self.width


class _Image(HorizontallyAlignedFlowable, ImageBase):
    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 dpi=None, rotate=0, limit_width=None, align=None,
                 id=None, style=None, parent=None):
        super().__init__(filename_or_file=filename_or_file, scale=scale,
                         width=width, height=height, dpi=dpi, rotate=rotate,
                         limit_width=limit_width, align=align,
                         id=id, style=style, parent=parent)



class Image(_Image):
    pass


class BackgroundImage(_Image, AttributeType):
    pass


class Caption(NumberedParagraph):
    @property
    def referenceable(self):
        return self.parent

    def text(self, container):
        label = self.parent.category + ' ' + self.number(container)
        return MixedStyledText(label + self.content, parent=self)


class FigureStyle(FloatStyle, GroupedFlowablesStyle):
    pass


class Figure(Float, InseparableFlowables, StaticGroupedFlowables):
    style_class = FigureStyle
    category = 'Figure'

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        document = flowable_target.document
        number = document.counters.setdefault(self.category, 1)
        document.counters[self.category] += 1
        for id in self.get_ids(document):
            document.set_reference(id, NUMBER, str(number))
            # TODO: need to store formatted number
            # document.set_reference(element_id, TITLE, caption text)
