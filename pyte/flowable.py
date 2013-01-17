
from .style import Style, Styled
from .dimension import PT


class FlowableStyle(Style):
    attributes = {'space_above': 0*PT,
                  'space_below': 0*PT}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Flowable(Styled):
    style_class = FlowableStyle

    def __init__(self, style=None):
        super().__init__(style)
        self.resume = False

    @property
    def page(self):
        return self.container.page

    @property
    def document(self):
        try:
            return self._document
        except AttributeError:
            return self.parent.document

    @document.setter
    def document(self, document):
        self._document = document

    def split(self):
        yield self

    def flow(self, container):
        """Flow this flowable into `container` and return the vertical space
        consumed."""
        start_offset = container._flowable_offset
        self.container = container
        if not self.resume:
            self.resume = True
            container.advance(float(self.get_style('space_above')))
        self.render(container)
        self.resume = False
        container.advance(float(self.get_style('space_below')))
        return container._flowable_offset - start_offset

    def render(self, canvas, offset=0):
        raise NotImplementedError("virtual method not implemented in class %s" %
                                  self.__class__.__name__)
