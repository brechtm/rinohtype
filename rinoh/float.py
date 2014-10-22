# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .flowable import Flowable, FlowableStyle, InseparableFlowables, StaticGroupedFlowables
from .inline import InlineFlowable
from .number import NumberedParagraph
from .reference import Referenceable, REFERENCE, TITLE
from .text import MixedStyledText


__all__ = ['InlineImage', 'Image', 'Caption', 'Figure']


LEFT = 'left'
CENTER = 'center'
RIGHT = 'right'


class HorizontallyAlignedFlowableStyle(FlowableStyle):
    attributes = {'horizontal_align': CENTER}


class HorizontallyAlignedFlowable(Flowable):
    style_class = HorizontallyAlignedFlowableStyle


class ImageBase(Flowable):
    def __init__(self, filename, scale=1.0, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.filename = filename
        self.scale = scale

    def left(self, image, container):
        raise NotImplementedError

    def render(self, container, last_descender, state=None):
        image = container.document.backend.Image(self.filename)
        if last_descender:
            container.advance(- last_descender)
        top = float(container.cursor)
        left = self.left(image, container)
        container.canvas.place_image(image, left, top, container.document,
                                     scale=self.scale)
        container.advance(float(image.height * self.scale))
        return image.width * self.scale, 0


class InlineImage(ImageBase, InlineFlowable):
    def left(self, image, container):
        return 0


class Image(ImageBase, HorizontallyAlignedFlowable):
    def left(self, image, container):
        align = self.get_style('horizontal_align', container.document)
        if align == LEFT:
            return 0
        elif align == RIGHT:
            return float(container.width)
        elif align == CENTER:
            return float(container.width - image.width * self.scale) / 2


class Caption(NumberedParagraph):
    @property
    def referenceable(self):
        return self.parent

    def text(self, document):
        label = self.parent.category + ' ' + self.number(document)
        return MixedStyledText(label + self.content, parent=self)


class Figure(Referenceable, StaticGroupedFlowables, InseparableFlowables):
    category = 'Figure'

    def prepare(self, document):
        super().prepare(document)
        element_id = self.get_id(document)
        number = document.counters.setdefault(__class__, 1)
        document.counters[__class__] += 1
        document.set_reference(element_id, REFERENCE, str(number))
        # TODO: need to store formatted number
        # document.set_reference(element_id, TITLE, caption text)
