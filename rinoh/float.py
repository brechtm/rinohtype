# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .flowable import Flowable, InseparableFlowables
from .number import format_number, NUMBER
from .paragraph import ParagraphBase, ParagraphState, ParagraphStyle
from .reference import Referenceable, Reference, REFERENCE, TITLE
from .text import MixedStyledText, NoBreakSpace


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


class CaptionStyle(ParagraphStyle):
    attributes = {'numbering_style': NUMBER,
                  'numbering_separator': '.'}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Caption(ParagraphBase):
    style_class = CaptionStyle

    next_number = {}

    def __init__(self, category, number, text, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.category = category
        self.number = number
        self.text = text

    def spans(self, document):
        numbering_style = self.get_style('numbering_style', document)
        separator = self.get_style('numbering_separator', document)
        if numbering_style is not None:
            formatted_number = format_number(self.number, numbering_style)
        else:
            formatted_number = ''
        label = self.category + ' ' + formatted_number + separator
        caption_text = label + NoBreakSpace() + self.text
        return MixedStyledText(caption_text, parent=self).spans()

    def render(self, container, last_descender, state=None):
        state = state or ParagraphState(self.spans(container.document))
        return super().render(container, last_descender, state=state)


class Figure(Referenceable, InseparableFlowables):
    def __init__(self, filename, caption, scale=1.0, style=None,
                 caption_style=None, id=None):
        self.image = Image(filename, scale=scale, parent=self)
        self.caption_text = caption
        self.caption_style = caption_style
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
        number = document.get_reference(self.get_id(document), REFERENCE)
        caption = Caption('Figure', number, self.caption_text, parent=self,
                          style=self.caption_style)
        return self.image, caption
