
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

    def flow(self, container):
        """Flow this flowable into `container` and return the vertical space
        consumed."""
        start_offset = container.cursor
        if not self.resume:
            self.resume = True
            container.advance(float(self.get_style('space_above')))
        self.render(container)
        self.resume = False
        container.advance(float(self.get_style('space_below')))
        return container.cursor - start_offset

    def render(self, container):
        raise NotImplementedError
