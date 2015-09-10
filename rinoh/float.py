# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .color import RED
from .dimension import PT
from .flowable import (Flowable, InseparableFlowables, StaticGroupedFlowables,
                       HorizontallyAlignedFlowable)
from .inline import InlineFlowable
from .number import NumberedParagraph
from .paragraph import Paragraph
from .reference import Referenceable, NUMBER
from .text import MixedStyledText, SingleStyledText, TextStyle


__all__ = ['InlineImage', 'Image', 'Caption', 'Figure']


LEFT = 'left'
CENTER = 'center'
RIGHT = 'right'


class ImageBase(Flowable):
    def __init__(self, filename_or_file, scale=1.0, width=None, rotate=0,
                 id=None, style=None, parent=None, **kwargs):
        super().__init__(id=id, style=style, parent=parent, **kwargs)
        self.filename_or_file = filename_or_file
        if scale != 1.0 and width is not None:
            raise TypeError('You should specify only one of scale and width')
        self.scale = scale
        self.width = width
        self.rotate = rotate

    def render(self, container, last_descender, state=None):
        try:
            image = container.document.backend.Image(self.filename_or_file)
        except OSError:
            message = "Image file not found: '{}'".format(self.filename_or_file)
            self.warn(message)
            text = SingleStyledText(message, style=TextStyle(font_color=RED))
            return Paragraph(text).render(container, last_descender)
        left, top = 0, float(container.cursor)
        if self.width is not None:
            width = self.width.to_points(container.width)
            scale = None
        else:
            width = None
            scale = self.scale
        w, h = container.canvas.place_image(image, left, top,
                                            container.document, scale=scale,
                                            width=width, rotate=self.rotate)
        container.advance(h)
        return w, 0


class InlineImage(ImageBase, InlineFlowable):
    def __init__(self, filename_or_file, scale=1.0, width=None, rotate=0,
                 baseline=0*PT, id=None, style=None, parent=None):
        super().__init__(filename_or_file, scale, width, rotate,
                         id, style, parent, baseline=baseline)


class Image(HorizontallyAlignedFlowable, ImageBase):
    pass


class Caption(NumberedParagraph):
    @property
    def referenceable(self):
        return self.parent

    def text(self, document):
        label = self.parent.category + ' ' + self.number(document)
        return MixedStyledText(label + self.content, parent=self)


class Figure(Referenceable, InseparableFlowables, StaticGroupedFlowables):
    category = 'Figure'

    def prepare(self, document):
        super().prepare(document)
        element_id = self.get_id(document)
        number = document.counters.setdefault(__class__, 1)
        document.counters[__class__] += 1
        document.set_reference(element_id, NUMBER, str(number))
        # TODO: need to store formatted number
        # document.set_reference(element_id, TITLE, caption text)
