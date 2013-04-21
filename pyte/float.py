
from .flowable import Flowable
from .number import format_number, NUMBER
from .paragraph import Paragraph, ParagraphStyle
from .reference import Referenceable
from .text import SingleStyledText, NoBreakSpace


__all__ = ['Image', 'CaptionStyle', 'Caption', 'Figure']


class Image(Flowable):
    def __init__(self, filename, scale=1.0, style=None):
        super().__init__(style)
        self.filename = filename
        self.scale = scale

    def render(self, container, last_descender):
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


class Caption(Paragraph):
    style_class = CaptionStyle

    next_number = {}

    def __init__(self, category, number, text, style=None):
        super().__init__('', style)
        numbering_style = self.get_style('numbering_style')
        numbering_sep = self.get_style('numbering_separator')
        if numbering_style is not None:
            self.ref = format_number(number, numbering_style)
            number = self.ref
        else:
            self.ref = None
            number = ''
        label = category + ' ' + number + numbering_sep
        caption_text = label + NoBreakSpace() + text
        self.append(caption_text)


class Figure(Flowable, Referenceable):
    def __init__(self, document, filename, caption, scale=1.0, style=None,
                 caption_style=None, id=None):
        self.number = document.counters.setdefault(self.__class__, 1)
        document.counters[self.__class__] += 1
        Flowable.__init__(self, style)
        Referenceable.__init__(self, document, id)
        self.filename = filename
        self.scale = scale
        self.caption = Caption('Figure', self.number, caption,
                               style=caption_style)

    def reference(self):
        return str(self.number)

    def title(self):
        return self.caption.text

    def render(self, container, last_descender):
        image = Image(self.filename, scale=self.scale)
        image_height = image.flow(container, None)
        caption_height = self.caption.flow(container, None)
