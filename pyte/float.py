
from .flowable import Flowable
from .number import format_number, NUMBER
from .paragraph import Paragraph, ParagraphStyle
from .reference import Referenceable
from .text import SingleStyledText


class Image(Flowable):
    def __init__(self, filename, scale=1.0, style=None):
        super().__init__(style)
        self.filename = filename
        self.scale = scale

    def render(self, canvas, offset=0):
        offset = self.container._flowable_offset
        canvas.save_state()
        image = canvas.document.backend.Image(self.filename)
        self.container.advance(image.height)
        canvas.translate((canvas.width - image.width) / 2,
                         canvas.height - offset - image.height)
        canvas.scale(self.scale)
        canvas.place_image(image)
        canvas.restore_state()
        return image.height


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
            number = self.ref + numbering_sep + '&nbsp;'
        else:
            self.ref = None
            number = ''
        styled_text = SingleStyledText(category + ' ' + number + text)
        styled_text.parent = self
        self.append(styled_text)


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

    def render(self, canvas, offset=0):
        image = Image(self.filename, scale=self.scale)
        image_height = self.container.flow(image)
        caption_height = self.container.flow(self.caption)
        return image_height + caption_height


class Float(object):
    def __init__(self, flowable):
        self.flowable = flowable
