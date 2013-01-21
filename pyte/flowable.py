"""

* :class:`FlowableStyle`:
* :class:`Flowable`:
* :class:`Floating`: Decorator to transform a :class:`Flowable` into a float

"""


from .style import Style, Styled
from .util import Decorator


class FlowableStyle(Style):
    attributes = {'space_above': 0,
                  'space_below': 0}


class Flowable(Styled):
    """"""

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


class Floating(Decorator):
    """Decorator to transform a :class:`Flowable` into a floating element. A
    floating element or 'float' is not flowed into its designated container, but
    is forwarded to another container, pointed to by the former's
    :attr:`Container.float_space` attribute.

    This is typically used to place figures and tables at the top or bottom of a
    page, instead of in between paragraphs."""

    def flow(self, container):
        """Flow this flowable into the float space associated with `container`.
        """
        super().flow(container.float_space)
        return 0
