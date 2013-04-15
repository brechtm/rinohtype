"""
The layout engine. The container classes allow defining rectangular areas on a
page to which :class:`Flowable`\ s can be rendered.

* :class:`Container`: A rectangular area on a page to which flowables are
                      rendered.
* :class:`DownExpandingContainer`: A container that dynamically grows downwards
                                   as flowables are rendered to it.
* :class:`UpExpandingContainer`: Similar to a :class:`DownExpandingContainer`:,
                                 but upwards expanding.
* :class:`VirtualContainer`: A container who's rendered content is not
                             automatically placed on the page. Afterwards, it
                             can be manually placed, however.
* :exc:`EndOfContainer`: Exception raised when a contianer "overflows" during
                         the rendering of flowables.
* :class:`Chain`: A chain of containers. When a container overflows, the
                  rendering of the chain's flowables is continued in the next
                  container in the chain.
"""


from .dimension import PT
from .util import cached_property


__all__ = ['Container', 'DownExpandingContainer', 'UpExpandingContainer',
           'VirtualContainer', 'Chain', 'EndOfContainer']
           # TODO: FootnoteContainer


class EndOfContainer(Exception):
    """The end of the :class:`Container` has been reached."""


class FlowableTarget(object):
    """Something that takes :class:`Flowable`\ s to be rendered."""

    def __init__(self, document):
        """Initialize this flowable target.

        `document` is the :class:`Document` this flowable target is part of."""
        self.flowables = []

        self.document = document
        """The :class:`Document` this flowable target is part of."""

    def append_flowable(self, flowable):
        """Append a `flowable` to the list of flowables to be rendered.

        This also updates `flowable` to hold a reference to the
        :class:`Document` this flowable target is part of."""
        flowable.document = self.document
        self.flowables.append(flowable)

    def __lshift__(self, flowable):
        """Shorthand for :meth:`append_flowable`. Returns `self` so that it can
        be chained."""
        self.append_flowable(flowable)
        return self

    def render(self):
        """Render the flowabless assigned to this flowable target, in the order
        that they have been added."""
        raise NotImplementedError


class ContainerBase(FlowableTarget):
    """Base class for containers that render :class:`Flowable`\ s to a
    rectangular area on a page. :class:`ContainerBase` takes care of the
    container's horizontal positioning and width. Its subclasses handle the
    vertical positioning and height."""

    def __init__(self, parent, left=None, width=None, right=None, chain=None):
        """Initialize a this container as a child of the `parent` container.

        The horizontal position and width of the container are determined from
        `left`, `width` and `right`. If only `left` or `right` are specified,
        the container's opposite edge will be placed at the corresponding edge
        of the parent container.

        Finally, `chain` is a :class:`Chain` this container will be appended to.
        """
        if left is None:
            left = 0*PT if (right and width) is None else (right - width)
        if width is None:
            width = (parent.width - left) if right is None else (right - left)
        self.left = left
        self.width = width
        self.right = left + width

        self.parent = parent
        if parent is not None:  # the Page subclass has no parent
            super().__init__(parent.document)
            parent.children.append(self)
        self.children = []
        self.flowables = []
        self.chain = chain
        if chain is not None:
            chain.append_container(self)

        self.cursor = 0     # initialized at the container's top edge
        """Keeps track of where the next flowable is to be placed. As flowables
        are flowed into the container, the cursor moves down."""

    @property
    def page(self):
        """The :class:`Page` this container is located on."""
        return self.parent.page

    @cached_property
    def canvas(self):
        """The canvas associated with this container."""
        return self.parent.canvas.new()

    @property
    def remaining_height(self):
        return self.height - self.cursor

    def advance(self, height):
        """Advance the cursor by `height`. If this would cause the cursor to
        point beyond the bottom of the container, an :class:`EndOfContainer`
        exception is raised."""
        self.cursor += height
        if self.cursor > self.height:
            raise EndOfContainer

    def render(self):
        """Render the contents of this container to its canvas. The contents
        include:

        1. the contents of child containers,
        2. :class:`Flowable`\ s that have been added to this container, and
        3. :class:`Flowable`\ s from the :class:`Chain` associated with this
           container.

        The rendering of the child containers (1) does not affect the rendering
        of the flowables (2 and 3). Therefore, a container typically has either
        children or flowables.
        On the other hand, the flowables from the chain are flowed following
        those assigned directly to this container, so it is possible to combine
        both.

        Note that the rendered contents need to be :meth:`place`d on the parent
        container's canvas before they become visible.

        This method returns an iterator yielding all the :class:`Chain`\ s that
        have run out of containers."""
        for child in self.children:
            for chain in child.render():
                yield chain
        last_descender = None
        for flowable in self.flowables:
            height, last_descender = flowable.flow(self, last_descender)
        if self.chain:
            for chain in self.chain.render():
                yield chain

    def place(self):
        """Place this container's canvas onto the parent container's canvas."""
        for child in self.children:
            child.place()
        self.canvas.append(float(self.left), float(self.top))


class Container(ContainerBase):
    """A container that renders :class:`Flowable`\ s to a rectangular area on a
    page. The first flowable is rendered at the top of the container. The next
    flowable is rendered below the first one, and so on.

    A :class:`Container` has an origin (the top-left corner), and a width and
    height. It's contents are rendered relative to the container's position in
    its parent :class:`Container`."""

    def __init__(self, parent, left=None, top=None, width=None, height=None,
                 right=None, bottom=None, chain=None):
        """Initialize this container as a child of the `parent` container.

        The horizontal position and width of the container are determined from
        `left`, `width` and `right`. If only `left` or `right` are specified,
        the container's opposite edge will be placed at the corresponding edge
        of the parent container.
        Similarly, the vertical position and height of the container are
        determined from `top`, `height` and `bottom`. If only one of `top` or
        `bottom` is specified, the container's opposite edge is placed at the
        corresponding edge of the parent container.

        Finally, `chain` is a :class:`Chain` this container will be appended to.
        """
        super().__init__(parent, left, width, right, chain)
        if top is None:
            top = 0*PT if (bottom and height) is None else (bottom - height)
        if height is None:
            height = (parent.height - top) if bottom is None else (bottom - top)
        self.top = top
        self.height = height
        self.bottom = top + height


class ExpandingContainer(ContainerBase):
    """An dynamically (vertically) growing version of the :class:`Container`."""

    def __init__(self, parent, left=None, width=None, right=None,
                 max_height=float('+inf'), chain=None):
        """Initialize this expanding container as a child of the `parent`
        container.

        See :class:`ContainerBase` for information on the `left`, `width` and
        `right` parameters. `max_height` is the maximum height this container
        can grow to."""
        super().__init__(parent, left, width, right, chain)
        self.max_height = max_height
        self.height = 0*PT

    @property
    def remaining_height(self):
        return self.max_height - self.cursor

    def advance(self, height):
        """Advance the cursor by `height`. If this would expand the container
        to become larger than its maximum height, an :class:`EndOfContainer`
        exception is raised."""
        self.cursor += height
        if self.max_height and self.cursor > self.max_height:
            raise EndOfContainer
        self._expand(height)

    def _expand(self, height):
        """Grow this container by `height`"""
        self.height += height


class DownExpandingContainer(ExpandingContainer):
    """A container that is anchored at the top and expands downwards."""

    def __init__(self, parent, left=None, top=None, width=None, right=None,
                 max_height=float('+inf'), chain=None):
        """Initialize this down-expanding container as a child of the `parent`
        container.

        The horizontal position and width of the container are determined from
        `left`, `width` and `right`. If only one of `left` or `right` is
        specified, the container's opposite edge will be placed at the
        corresponding edge of the parent container.
        `top` specifies the location of the container's top edge with respect to
        that of the parent container. When `top` is omitted, the top edge falls
        together with the top edge of the parent container.
        `max_height` is the maximum height this container can grow to."""
        super().__init__(parent, left, width, right, max_height, chain)
        self.top = top if top is not None else 0*PT
        self.bottom = self.top + self.height


class UpExpandingContainer(ExpandingContainer):
    """A container that is anchored at the bottom and expands upwards."""

    def __init__(self, parent, left=None, bottom=None, width=None, right=None,
                 max_height=float('+inf'), chain=None):
        """Initialize this up-expanding container as a child of the `parent`
        container.

        The horizontal position and width of the container are determined from
        `left`, `width` and `right`. If only one of `left` or `right` is
        specified, the container's opposite edge will be placed at the
        corresponding edge of the parent container.
        `bottom` specifies the location of the container's bottom edge with
        respect to that of the parent container. When `bottom` is omitted, the
        bottom edge falls together with the bottom edge of the parent container.
        `max_height` is the maximum height this container can grow to."""
        super().__init__(parent, left, width, right, max_height, chain)
        self.bottom = bottom if bottom is not None else parent.height
        self.top = self.bottom - self.height


class VirtualContainer(DownExpandingContainer):
    """A down-expanding container who's contents are rendered, but not placed on
    the parent container's canvas afterwards. It can later be placed manually by
    using the :meth:`Canvas.append` method of the container's :class:`Canvas`.
    """

    def __init__(self, parent, width):
        """Initialize this virtual container as a child of the `parent`
        container.

        `width` specifies the width of the container."""
        super().__init__(parent, width=width)

    def place(self):
        """This method has no effect."""
        pass


class FootnoteContainer(UpExpandingContainer):
    def __init__(self, parent, left=None, bottom=None, width=None, right=None):
        super().__init__(parent, left, bottom, width=width, right=right)
        self._footnote_number = 0

    @property
    def next_number(self):
        self._footnote_number += 1
        return self._footnote_number


class Chain(FlowableTarget):
    """A :class:`FlowableTarget` that renders its flowables to a series of
    containers. Once a container is filled, the chain starts flowing flowables
    into the next container."""

    def __init__(self, document):
        """Initialize this chain.

        `document` is the :class:`Document` this chain is part of."""
        super().__init__(document)
        self._init_state()

    def _init_state(self):
        """Reset the state of this chain: empty the list of containers, and zero
        the counter keeping track of which flowable needs to be rendered next.
        """
        self._containers = []
        self._container_index = 0
        self._flowable_index = 0

    def render(self):
        """Flow the flowables into the containers that have been added to this
        chain.

        Returns an empty iterator when all flowables have been sucessfully
        rendered.
        When the chain runs out of containers before all flowables have been
        rendered, this method returns an iterator yielding itself. This signals
        the :class:`Document` to generate a new page and register new containers
        with this chain."""
        while self._container_index < len(self._containers):
            container = self._containers[self._container_index]
            last_descender = None
            self._container_index += 1
            try:
                while self._flowable_index < len(self.flowables):
                    flowable = self.flowables[self._flowable_index]
                    height, last_descender = flowable.flow(container,
                                                           last_descender)
                    self._flowable_index += 1
            except EndOfContainer:
                if self._container_index > len(self._containers) - 1:
                    yield self
        self._init_state()      # reset the state for the next rendering loop

    def append_container(self, container):
        """Append `container` to the list of containers in this chain."""
        self._containers.append(container)
