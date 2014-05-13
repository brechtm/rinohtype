# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .flowable import Flowable, InseparableFlowables
from .number import NumberedParagraph, NumberStyle
from .paragraph import ParagraphState, ParagraphStyle
from .reference import Referenceable, REFERENCE, TITLE
from .text import MixedStyledText


__all__ = ['Image', 'CaptionStyle', 'Caption', 'Figure']


class Image(Flowable):
    def __init__(self, filename, scale=1.0, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.filename = filename
        self.scale = scale

    def render(self, container, last_descender, state=None):
        image = container.canvas.document.backend.Image(self.filename)
        left = float(container.width - image.width) / 2
        top = float(container.cursor)
        container.canvas.place_image(image, left, top, scale=self.scale)
        container.advance(float(image.height))
        return image.width, 0


class CaptionStyle(ParagraphStyle, NumberStyle):
    pass


class Caption(NumberedParagraph):
    style_class = CaptionStyle

    def text(self, document):
        label = self.parent.category + ' ' + self.number(document)
        return MixedStyledText(label + self.content, parent=self)


class Figure(Referenceable, InseparableFlowables):
    category = 'Figure'

    def __init__(self, filename, caption, scale=1.0, style=None, id=None):
        self.image = Image(filename, scale=scale, parent=self)
        self.caption_text = caption
        InseparableFlowables.__init__(self, style)
        Referenceable.__init__(self, id)

    def prepare(self, document):
        super().prepare(document)
        element_id = self.get_id(document)
        number = document.counters.setdefault(__class__, 1)
        document.counters[__class__] += 1
        document.set_reference(element_id, REFERENCE, str(number))
        # TODO: need to store formatted number
        document.set_reference(element_id, TITLE, self.caption_text)

    def flowables(self, document):
        caption = Caption(self.caption_text, parent=self)
        return self.image, caption
