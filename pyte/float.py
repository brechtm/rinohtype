
from psg.drawing.box import canvas, eps_image

from .flowable import Flowable
from .paragraph import Paragraph
from .unit import mm


class Figure(Flowable):
    def __init__(self, filename, scale=1.0, style=None):
        super().__init__(style)
        self.filename = filename
        self.scale = scale

    def render(self, pscanvas, offset=0):
        buffer = canvas(pscanvas, 0, 0, pscanvas.w(), pscanvas.h())
        eps = eps_image(buffer, open(self.filename, 'rb'), document_level=True)
        image_height = eps.h() * self.scale
        image_width = eps.w() * self.scale
        image_canvas = canvas(pscanvas, (pscanvas.w() - image_width) / 2,
                              pscanvas.h() - offset - image_height,
                              pscanvas.w(), pscanvas.h())
        buffer.write_to(image_canvas)
        image_canvas.append(eps)
        image_canvas.push('{0} {0} scale'.format(self.scale))
        image_canvas.write_to(pscanvas)

        return image_height


##class CaptionStyle(ParagraphStyle):
##    attributes = {'numberingStyle': NumberingStyle.number,
##                  'numberingSeparator': '.'}
##
##    def __init__(self, name, base=None, **attributes):
##        super().__init__(name, base=base, **attributes)
##
##
##class Caption(Paragraph):
##    style_class = CaptionStyle
##
##    next_number = {}
##
##    def __init__(self, text, category, style=None):
##        next_number = self.next_number.setdefault(category, 1)
##        if style.numberingStyle is not None:
##            self.ref = self._format_number(self.next_number[level],
##                                           style.numberingStyle)
##            number = self.ref + style.numberingSeparator + '&nbsp;'
##        else:
##            self.ref = None
##            number = ""
##        if level in self.next_number:
##            self.next_number[level] += 1
##            self.next_number[level + 1] = 1
##        else:
##            self.next_number[level] = 2
##        self.level = level
##        super().__init__(number + title, style)
##
##
##class Figure(Flowable):
##    def __init__(self, filename, scale=1.0, style=None, captionstyle=None):
##        super().__init__(style)
##        self.filename = filename
##        self.scale = scale
##
##    def render(self, pscanvas, offset=0):
##        image = Image(self.filename, scale=self.scale)
##        image.render(pscanvas)
