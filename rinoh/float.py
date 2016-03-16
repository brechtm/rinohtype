# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .color import RED
from .dimension import PT
from .flowable import (Flowable, InseparableFlowables, StaticGroupedFlowables,
                       HorizontallyAlignedFlowable,
                       HorizontallyAlignedFlowableState)
from .inline import InlineFlowable
from .layout import EndOfContainer
from .number import NumberedParagraph
from .paragraph import Paragraph
from .reference import Referenceable, NUMBER
from .style import AttributeType
from .text import MixedStyledText, SingleStyledText, TextStyle
from .util import ReadAliasAttribute


__all__ = ['InlineImage', 'Image', 'Caption', 'Figure']


LEFT = 'left'
CENTER = 'center'
RIGHT = 'right'

FIT = 'fit'


class ImageState(HorizontallyAlignedFlowableState):
    image = ReadAliasAttribute('flowable')
    width = None


class ImageBase(Flowable):
    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 rotate=0, id=None, style=None, parent=None, **kwargs):
        super().__init__(id=id, style=style, parent=parent, **kwargs)
        self.filename_or_file = filename_or_file
        if width is not None and height is not None and scale != 1.0:
            raise TypeError('Scale may not be specified when either width or '
                            'height are given.')
        self.scale = scale
        self.height = height
        self.width = width
        self.rotate = rotate

    def initial_state(self, container):
         return ImageState(self)

    def render(self, container, last_descender, state):
        try:
            image = container.document.backend.Image(self.filename_or_file)
        except OSError as err:
            message = "Error opening image file: {}".format(err)
            self.warn(message)
            text = SingleStyledText(message, style=TextStyle(font_color=RED))
            return Paragraph(text).render(container, last_descender)
        left, top = 0, float(container.cursor)
        if self.width is not None:
            scale_width = self.width.to_points(container.width) / image.width
        else:
            scale_width = None
        if self.height is not None:
            scale_height = self.height.to_points(container.width) / image.height
            if scale_width is None:
                scale_width = scale_height
        else:
            scale_height = scale_width
        if scale_width is None:
            if self.scale == FIT:
                scale = min(float(container.width) / image.width,
                            float(container.remaining_height) / image.height)
                scale_width = scale_height = scale

            else:
                scale_width = scale_height = self.scale
        w, h = container.canvas.place_image(image, left, top,
                                            container.document, scale_width,
                                            scale_height, self.rotate)
        ignore_overflow = (self.scale == FIT) or (not state.initial)
        try:
            container.advance(h, ignore_overflow)
        except EndOfContainer:
            state.initial = False
            raise EndOfContainer(state)
        return w, 0


class InlineImage(ImageBase, InlineFlowable):
    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 rotate=0, baseline=0*PT, id=None, style=None, parent=None):
        super().__init__(filename_or_file=filename_or_file, scale=scale,
                         width=width, height=height, rotate=rotate,
                         id=id, style=style, parent=parent, baseline=baseline)


class _Image(HorizontallyAlignedFlowable, ImageBase):
    def __init__(self, filename_or_file, scale=1.0, width=None, height=None,
                 rotate=0, align=None, id=None, style=None, parent=None):
        super().__init__(filename_or_file=filename_or_file, scale=scale,
                         width=width, height=height, rotate=rotate, align=align,
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


class Figure(Referenceable, InseparableFlowables, StaticGroupedFlowables):
    category = 'Figure'

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        document = flowable_target.document
        element_id = self.get_id(document)
        number = document.counters.setdefault(self.category, 1)
        document.counters[self.category] += 1
        document.set_reference(element_id, NUMBER, str(number))
        # TODO: need to store formatted number
        # document.set_reference(element_id, TITLE, caption text)
