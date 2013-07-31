"""
Base classes for flowable and floating document elements. These are elements
that make up the content of a document and are rendered onto its pages.

* :class:`Flowable`: Element that is rendered onto a :class:`Container`.
* :class:`FlowableStyle`: Style class specifying the vertical space surrounding
                          a :class:`Flowable`.
* :class:`Floating`: Decorator to transform a :class:`Flowable` into a floating
                     element.
"""


from .layout import EndOfContainer, DownExpandingContainer, MaybeContainer
from .style import Style, Styled
from .util import Decorator


__all__ = ['Flowable', 'FlowableStyle', 'Floating']


class FlowableException(Exception):
    pass


class FlowableStyle(Style):
    """The :class:`Style` for :class:`Flowable` objects. It has the following
    attributes:

    * `space_above`: Vertical space preceding the flowable (:class:`Dimension`)
    * `space_below`: Vertical space following the flowable (:class:`Dimension`)
    * `indent_left`: Left indentation of text (class:`Dimension`).
    * `indent_right`: Right indentation of text (class:`Dimension`).
    """

    attributes = {'space_above': 0,
                  'space_below': 0,
                  'indent_left': 0,
                  'indent_right': 0}


class Flowable(Styled):
    """An element that can be 'flowed' into a :class:`Container`. A flowable can
    adapt to the width of the container, or it can horizontally align itself in
    the container."""

    style_class = FlowableStyle

    def __init__(self, style=None, parent=None):
        """Initialize this flowable and associate it with the given `style` and
        `parent` (see :class:`Styled`)."""
        super().__init__(style=style, parent=parent)
        self.resume = False

    def flow(self, container, last_descender, state=None):
        """Flow this flowable into `container` and return the vertical space
        consumed.

        The flowable's contents is preceded by a vertical space with a height
        as specified in its style's `space_above` attribute. Similarly, the
        flowed content is followed by a vertical space with a height given
        by the `space_below` style attribute."""
        start_offset = container.cursor
        if not self.resume:
            self.resume = True
            container.advance(float(self.get_style('space_above')))
        left = self.get_style('indent_left')
        right = container.width - self.get_style('indent_right')
        max_height = container.remaining_height
        pad_container = DownExpandingContainer('PADDED',
                                               container,
                                               top=container.cursor,
                                               left=left, right=right,
                                               max_height=max_height)
        last_descender = self.render(pad_container, last_descender, state=state)
        container.advance(pad_container.cursor)
        self.resume = False
        try:
            container.advance(float(self.get_style('space_below')))
        except EndOfContainer:
            pass
        return container.cursor - start_offset, last_descender

    @property
    def width(self):
        """Raises :class:`FlowableException`.
        (accessed when this flowable is embedded in a paragraph)"""
        raise FlowableException

    def spans(self):
        """Generator yielding this flowable itself.
        (called when this flowable is embedded in a paragraph)"""
        yield self

    def render(self, container, descender, state=None):
        """Renders the flowable's content to `container`, with the flowable's
        top edge lining up with the container's cursor. `descender` is the
        descender height of the preceeding line or `None`."""
        raise NotImplementedError


class FlowableState(object):
    """Stores a :class:`Flowable`\'s rendering state, which can be copied. This
    enables saving the rendering state at certain points in the rendering
    process, so rendering can later be resumed at those points, if needed."""

    def __copy__(self):
        raise NotImplementedError


class GroupedFlowables(Flowable):
    def __init__(self, flowables, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.flowables = flowables

    def render(self, container, last_descender, state=None):
        maybe_container = MaybeContainer(container)
        for flowable in self.flowables:
            height, last_descender = flowable.flow(maybe_container,
                                                   last_descender)
        maybe_container.do_place()
        return last_descender


class Floating(Decorator):
    """Decorator to transform a :class:`Flowable` into a floating element. A
    floating element or 'float' is not flowed into its designated container, but
    is forwarded to another container, pointed to by the former's
    :attr:`Container.float_space` attribute.

    This is typically used to place figures and tables at the top or bottom of a
    page, instead of in between paragraphs."""

    def flow(self, container, last_descender, state=None):
        """Flow this flowable into the float space associated with `container`.
        """
        if self not in container.document.floats:
            super().flow(container.float_space, None)
            container.document.floats.add(self)
            container.page.check_overflow()
        return 0, last_descender
