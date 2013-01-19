
from .dimension import PT
from .util import cached_property


__all__ = ['Container', 'DownExpandingContainer', 'UpExpandingContainer',
           'VirtualContainer', 'Chain', 'EndOfContainer']
           # TODO: FootnoteContainer


class EndOfContainer(Exception):
    """The end of the :class:`Container` has been reached."""



class RenderTarget(object):
    """Something that takes :class:`Flowable`\ s to be rendered."""

    def __init__(self):
        self.flowables = []

    @property
    def document(self):
        """Return the :class:`Document` this :class:`RenderTarget` is part of.
        """
        raise NotImplementedError

    def add_flowable(self, flowable):
        """Add a :class:`Flowable` to be rendered by this :class:`RenderTarget`.
        """
        flowable.document = self.document
        self.flowables.append(flowable)

    def render(self):
        """Render the :class:`Flowable`\ s assigned to this
        :class:`RenderTarget`, in the order that they have been added."""
        raise NotImplementedError


class ContainerBase(RenderTarget):
    """Base class for containers that render :class:`Flowable`\ s to a
    rectangular area on a page. :class:`ContainerBase` takes care of the
    container's horizontal positioning and width. Its subclasses handle its
    vertical positioning and height.

    The container has a ´cursor´ attribute that keeps track of where the next
    flowable is to be placed. As flowables are flowed into the container, the
    cursor moves down."""

    def __init__(self, parent, left=None, width=None, right=None, chain=None):
        """Initialize a this container as a child of the `parent` container.

        The horizontal position and width of the container are determined from
        `left`, `width` and `right`. If only `left` or `right` are specified,
        the container's other opposite edge will be placed at the corresponding
        edge of the parent container.

        `chain` is a :class:`Chain` this container will be appended to."""
        self.parent = parent
        if parent:
            parent.children.append(self)

        if left is None:
            left = 0*PT if (right and width) is None else (right - width)
        if width is None:
            width = (parent.width - left) if right is None else (right - left)
        self.left = left
        self.width = width
        self.right = left + width

        self.children = []
        self.flowables = []
        self.chain = chain
        if chain is not None:
            chain.add_container(self)
        self.cursor = 0   # initialized at the container's top edge

    @property
    def page(self):
        """The :class:`Page` this container is located on."""
        return self.parent.page

    @property
    def document(self):
        """The :class:`Document` this container is part of."""
        return self.page.document

    @cached_property
    def canvas(self):
        """The canvas associated with this container."""
        return self.parent.canvas.new()

    def advance(self, height):
        """Advance the cursor by `height`. The cursor determines the location
        where the next flowable is placed."""
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
        of the flowables (2 and 3). Therefore, a container typically either has
        only children or only flowables.
        On the other hand, the flowables from the chain are flowed following
        those assigned directly to this container, so it is possible to combine
        both.

        This method returns an iterator yielding all the :class:`Chain`s that
        have run out of containers."""
        for child in self.children:
            for chain in child.render():
                yield chain
        for flowable in self.flowables:
            flowable.flow(self)
        if self.chain:
            for chain in self.chain.render():
                yield chain

    def place(self):
        """Place the container's canvas at the correct location onto the canvas
        of its parent container."""
        for child in self.children:
            child.place()
        self.canvas.append(float(self.left), float(self.top))


class Container(ContainerBase):
    """A container that renders :class:`Flowable`\ s to a rectangular area on a
    page.

    A :class:`Container` has an origin (the top-left corner), and a width and
    height. It's contents (:class:`Flowable`\ s) are rendered relative to the
    :class:`Container`'s position in its parent :class:`Container`."""

    def __init__(self, parent, left=None, top=None,
                 width=None, height=None, right=None, bottom=None,
                 chain=None):
        """Initialize a :class:`Container` as a child of the `parent`
        :class:`Container`. `left` and `top` establish the position of
        this :class:`Container`'s top-left origin relative to that of its parent
        :class:`Container`.

        Optionally, `width` and `height` specify the size of the
        :class:`Container`. If equal to `None`, the :class:`Container` fills up
        the available space in the parent :class:`Container`.

        In stead of `width` and `height`, `right` and `bottom` can be specified
        to pass the abolute coordinates of the right and bottom edges of the
        :class:`Container`.

        Finally, `chain` is a :class:`Chain` this :class:`Container` will be
        appended to."""
        super().__init__(parent, left, width, right, chain)
        if top is None:
            top = 0*PT if (bottom and height) is None else (bottom - height)
        if height is None:
            height = (parent.height - top) if bottom is None else (bottom - top)
        self.top = top
        self.height = height
        self.bottom = top + height


class ExpandingContainer(ContainerBase):
    def __init__(self, parent, left=None, width=None, right=None,
                 max_height=None, chain=None):
        super().__init__(parent, left, width, right, chain)
        self.max_height = max_height
        self.height = 0*PT

    def advance(self, height):
        self.cursor += height
        if self.max_height and self.cursor > self.max_height:
            raise EndOfContainer
        self.expand(height)

    def expand(self, height):
        self.height += height


class DownExpandingContainer(ExpandingContainer):
    def __init__(self, parent, left=None, top=None, width=None, right=None,
                 max_height=None, chain=None):
        super().__init__(parent, left, width, right, max_height, chain)
        self.top = top if top is not None else 0*PT

    @property
    def bottom(self):
        return self.top + self.height


class UpExpandingContainer(ExpandingContainer):
    def __init__(self, parent, left=None, bottom=None, width=None, right=None,
                 max_height=None, chain=None):
        super().__init__(parent, left, width, right, max_height, chain)
        self.bottom = bottom

    @property
    def top(self):
        return self.bottom - self.height


class FootnoteContainer(UpExpandingContainer):
    def __init__(self, parent, left=0*PT, bottom=0*PT, width=None, right=None):
        super().__init__(parent, left, bottom, width=width, right=right)
        self._footnote_number = 0

    @property
    def next_number(self):
        self._footnote_number += 1
        return self._footnote_number


class VirtualContainer(DownExpandingContainer):
    def __init__(self, parent, width):
        super().__init__(parent, width=width)

    def place(self):
        pass


class Chain(RenderTarget):
    def __init__(self, document):
        super().__init__()
        self._document = document
        self._containers = []
        self._container_index = 0
        self._flowable_index = 0

    @property
    def document(self):
        return self._document

    def render(self):
        while self._container_index < len(self._containers):
            container = self._containers[self._container_index]
            self._container_index += 1
            try:
                while self._flowable_index < len(self.flowables):
                    flowable = self.flowables[self._flowable_index]
                    flowable.flow(container)
                    self._flowable_index += 1
            except EndOfContainer:
                if self._container_index > len(self._containers) - 1:
                    yield self

    def add_container(self, container):
        self._containers.append(container)
