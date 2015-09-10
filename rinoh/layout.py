# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

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
* :class:`FootnoteContainer`: TODO

"""

from collections import deque
from contextlib import contextmanager
from copy import copy

from .dimension import Dimension, PT, DimensionAddition


__all__ = ['Container', 'FlowablesContainer', 'ChainedContainer',
           'DownExpandingContainer', 'InlineDownExpandingContainer',
           'UpExpandingContainer', 'VirtualContainer', 'Chain',
           'EndOfContainer', 'FootnoteContainer', 'MaybeContainer',
           'discard_state']


class EndOfContainer(Exception):
    """The end of the :class:`FlowableContainer` has been reached."""

    def __init__(self, flowable_state=None, page_break=False):
        """`flowable_state` represents the rendering state of the
        :class:`Flowable` at the time the :class:`FlowableContainer`" overflows.
        """
        self.flowable_state = flowable_state
        self.page_break = page_break


class ReflowRequired(Exception):
    """Reflow of the current page is required due to insertion of a float."""


class FlowableTarget(object):
    """Something that takes :class:`Flowable`\ s to be rendered."""

    def __init__(self, document_part, *args, **kwargs):
        """Initialize this flowable target.

        `document_part` is the :class:`Document` this flowable target is part
        of."""
        self.flowables = []
        document_part.flowable_targets.append(self)
        super().__init__(*args, **kwargs)

    def append_flowable(self, flowable):
        """Append a `flowable` to the list of flowables to be rendered."""
        self.flowables.append(flowable)

    def __lshift__(self, flowable):
        """Shorthand for :meth:`append_flowable`. Returns `self` so that it can
        be chained."""
        self.append_flowable(flowable)
        return self

    def prepare(self, document):
        for flowable in self.flowables:
            flowable.prepare(document)

    def render(self):
        """Render the flowables assigned to this flowable target, in the order
        that they have been added."""
        raise NotImplementedError


class Container(object):
    """Rectangular area that contains elements to be rendered to a
    :class:`Page`. A :class:`Container` has an origin (the top-left corner), a
    width and a height. It's contents are rendered relative to the container's
    position in its parent :class:`Container`."""

    def __init__(self, name, parent, left=None, top=None, width=None,
                 height=None, right=None, bottom=None):
        """Initialize a this container as a child of the `parent` container.

        The horizontal position and width of the container are determined from
        `left`, `width` and `right`. If only `left` or `right` is specified,
        the container's opposite edge will be placed at the corresponding edge
        of the parent container.

        Similarly, the vertical position and height of the container are
        determined from `top`, `height` and `bottom`. If only one of `top` or
        `bottom` is specified, the container's opposite edge is placed at the
        corresponding edge of the parent container."""
        if left is None:
            left = 0*PT if (right and width) is None else (right - width)
        if width is None:
            width = (parent.width - left) if right is None else (right - left)
        if right is None:
            right = left + width
        self.left = left
        self.width = width
        self.right = right

        if top is None:
            top = 0*PT if (bottom and height) is None else (bottom - height)
        if height is None:
            height = (parent.height - top) if bottom is None else (bottom - top)
        if bottom is None:
            bottom = top + height
        self.top = top
        self.height = height
        self.bottom = bottom

        self.name = name
        self.parent = parent
        if parent is not None:
            self.parent.children.append(self)
        self.children = []
        self.clear()

    @property
    def document_part(self):
        return self.parent.document_part

    @property
    def document(self):
        return self.document_part.document

    def clear(self):
        self.empty_canvas()

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)

    def __getattr__(self, name):
        if name in ('_footnote_space', 'float_space'):
            return getattr(self.parent, name)
        raise AttributeError(name)

    @property
    def page(self):
        """The :class:`Page` this container is located on."""
        return self.parent.page

    def empty_canvas(self):
        self.canvas = self.parent.canvas.new()

    def render(self, rerender=False):
        """Render the contents of this container to its canvas.

        Note that the rendered contents need to be :meth:`place`d on the parent
        container's canvas before they become visible.

        This method returns an iterator yielding all the :class:`Chain`\ s that
        have run out of containers."""
        for child in self.children:
            for chain in child.render(rerender):
                yield chain

    def check_overflow(self):
        for child in self.children:
            child.check_overflow()

    def place_children(self):
        for child in self.children:
            child.place()

    def place(self):
        """Place this container's canvas onto the parent container's canvas."""
        self.place_children()
        self.canvas.append(float(self.left), float(self.top))


class FlowablesContainerBase(Container):
    """A :class:`Container` that renders :class:`Flowable`\ s to a rectangular
    area on a page. The first flowable is rendered at the top of the container.
    The next flowable is rendered below the first one, and so on."""

    def __init__(self, name, parent, left=None, top=None, width=None, height=None,
                 right=None, bottom=None):
        self._self_cursor = Dimension(0)  # initialized at container's top edge
        self._cursor = DimensionAddition(self._self_cursor)
        super().__init__(name, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom)

    @property
    def chained_ancestor(self):
        return self.parent.chained_ancestor

    def clear(self):
        super().clear()
        del self.children[:]
        self._self_cursor._value = 0  # initialized at container's top edge
        del self._cursor.addends[1:]

    @property
    def cursor(self):
        """Keeps track of where the next flowable is to be placed. As flowables
        are flowed into the container, the cursor moves down."""
        return float(self._cursor)

    @property
    def remaining_height(self):
        return self.height - self.cursor

    def render(self, rerender=False):
        raise NotImplementedError

    def advance(self, height, ignore_overflow=False):
        """Advance the cursor by `height`. If this would cause the cursor to
        point beyond the bottom of the container, an :class:`EndOfContainer`
        exception is raised."""
        if height <= self.remaining_height:
            self._self_cursor.grow(height)
        elif not ignore_overflow:
            raise EndOfContainer

    def check_overflow(self):
        if self.remaining_height < 0:
            raise ReflowRequired


class FlowablesContainer(FlowableTarget, FlowablesContainerBase):
    """A container that renders a predefined series of flowables."""

    def __init__(self, name, parent, left=None, top=None, width=None,
                 height=None, right=None, bottom=None):
        super().__init__(parent.document_part, name, parent, left=left, top=top,
                         width=width, height=height, right=right, bottom=bottom)

    def render(self, rerender=False):
        if not self.cursor:
            last_descender = None
            for flowable in self.flowables:
                height, last_descender = flowable.flow(self, last_descender)
        return iter(())   # no chains to yield


class ChainedContainer(FlowablesContainerBase):
    """A container that renders flowables from the :class:`Chain` it is part
    of."""

    def __init__(self, name, parent, chain, left=None, top=None, width=None,
                 height=None, right=None, bottom=None):
        super().__init__(name, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom)
        chain.containers.append(self)
        self.chain = chain

    @property
    def chained_ancestor(self):
        return self

    def render(self, rerender=False):
        last_descender = None
        if self.chain.render(self, rerender=rerender,
                             last_descender=last_descender):
            yield self.chain


class ExpandingContainer(FlowablesContainer):
    """A dynamically, vertically growing :class:`Container`."""

    def __init__(self, name, parent, left=None, top=None, width=None,
                 right=None, bottom=None, max_height=None):
        """See :class:`ContainerBase` for information on the `parent`, `left`,
        `width` and `right` parameters.

        `max_height` is the maximum height this container can grow to."""
        height = DimensionAddition()
        super().__init__(name, parent, left, top, width, height, right, bottom)
        self.height.addends.append(self._cursor)
        self.max_height = max_height or float('+inf')

    @property
    def remaining_height(self):
        return self.max_height - self.cursor


class DownExpandingContainer(ExpandingContainer):
    """A container that is anchored at the top and expands downwards."""


class InlineDownExpandingContainer(DownExpandingContainer):
    def __init__(self, name, parent, left=None, width=None, right=None,
                 extra_space_below=0, advance_parent=True):
        super().__init__(name, parent, left=left, top=parent.cursor,
                         width=width, right=right,
                         max_height=parent.remaining_height)
        if advance_parent:
            parent._cursor.addends.append(self._cursor)
        self.extra_space_below = extra_space_below

    @property
    def remaining_height(self):
        return super().remaining_height - self.extra_space_below

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        self.advance(self.extra_space_below)


class UpExpandingContainer(ExpandingContainer):
    """A container that is anchored at the bottom and expands upwards."""

    def __init__(self, name, parent, left=None, bottom=None, width=None,
                 right=None, max_height=None, extra_space_below=0):
        """See :class:`ContainerBase` for information on the `parent`, `left`,
        `width` and `right` parameters.

        `bottom` specifies the location of the container's bottom edge with
        respect to that of the parent container. When `bottom` is omitted, the
        bottom edge is placed at the bottom edge of the parent container.

        `max_height` is the maximum height this container can grow to."""
        bottom = bottom or parent.height
        super().__init__(name, parent, left, None, width, right, bottom,
                         max_height)


class MaybeContainer(InlineDownExpandingContainer):
    def __init__(self, parent, left=None, width=None, right=None):
        super().__init__('MAYBE', parent, left=left, width=width, right=right)
        self._do_place = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, _):
        if (exc_type is None
            or (issubclass(exc_type, EndOfContainer)
                and (exc_value.flowable_state
                     and not exc_value.flowable_state.initial))):
            self.do_place()

    def do_place(self):
        self._do_place = True

    def place(self):
        if self._do_place:
            super().place()


@contextmanager
def discard_state():
    try:
        yield
    except EndOfContainer:
        raise EndOfContainer


class VirtualContainer(DownExpandingContainer):
    """An infinitely down-expanding container whose contents are not
    automatically placed on the canvas of the parent container's canvas. This
    container's content needs to be placed explicitly using :meth:`place_at`."""

    def __init__(self, parent, width=None):
        """`width` specifies the width of the container."""
        super().__init__('VIRTUAL', parent, width=width, max_height=float('+inf'))

    def empty_canvas(self):
        self.canvas = self.document.backend.Canvas(None)

    def place(self):
        """This method has no effect."""

    def place_at(self, container, left, top):
        self.place_children()
        self.canvas.parent = container.canvas
        self.canvas.append(float(left), float(top))



class FloatContainer(ExpandingContainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TopFloatContainer(FloatContainer, DownExpandingContainer):
    def __init__(self, name, parent, left=None, top=None, width=None,
                 right=None, max_height=None):
        super().__init__(name, parent, left, top, width, right, max_height)


class BottomFloatContainer(UpExpandingContainer, FloatContainer):
    def __init__(self, name, parent, left=None, bottom=None, width=None,
                 right=None, max_height=None):
        super().__init__(name, parent, left, bottom, width, right, max_height)


class FootnoteContainer(UpExpandingContainer):
    def __init__(self, name, parent, left=None, bottom=None, width=None,
                 right=None, max_height=None):
        super().__init__(name, parent, left, bottom, width=width, right=right,
                         max_height=max_height)
        self._footnote_number = 0
        self._footnote_space = self
        self.footnote_queue = deque()
        self._flowing_footnotes = False
        self._reflowed = False
        self._descenders = [0]

    def add_footnote(self, footnote):
        self.footnote_queue.append(footnote)
        if not self._flowing_footnotes:
            try:
                self.flow_footnotes()
            finally:
                self._flowing_footnotes = False

    def flow_footnotes(self):
        if self._reflowed:
            self._cursor.addends.pop()
            self._descenders.pop()
        while self.footnote_queue:
            footnote = self.footnote_queue.popleft()
            footnote_id = footnote.get_id(self.document)
            if footnote_id not in self.document.placed_footnotes:
                with MaybeContainer(self) as maybe_container:
                    _, descender = footnote.flow(maybe_container,
                                                 self._descenders[-1])
                    self._descenders.append(descender)
                    self._reflowed = True
                    self.page.check_overflow()
                    self._reflowed = False
                    self.document.placed_footnotes.add(footnote_id)
    @property
    def next_number(self):
        self._footnote_number += 1
        return self._footnote_number


class ChainState(object):
    def __init__(self, flowable_index=0, flowable_state=None):
        self.flowable_index = flowable_index
        self.flowable_state = flowable_state

    def __copy__(self):
        return self.__class__(self.flowable_index, copy(self.flowable_state))

    def next_flowable(self):
        self.flowable_index += 1
        self.flowable_state = None


class Chain(FlowableTarget):
    """A :class:`FlowableTarget` that renders its flowables to a series of
    containers. Once a container is filled, the chain starts flowing flowables
    into the next container."""

    def __init__(self, document_part):
        """Initialize this chain.

        `document` is the :class:`Document` this chain is part of."""
        super().__init__(document_part)
        self._init_state()
        self._page_to_break = None
        self.containers = []

    def _init_state(self):
        """Reset the state of this chain: empty the list of containers, and zero
        the counter keeping track of which flowable needs to be rendered next.
        """
        self._state = ChainState()
        self._fresh_page_state = copy(self._state)
        self._rerendering = False

    @property
    def last_container(self):
        return self.containers[-1]

    def render(self, container, rerender=False, last_descender=None):
        """Flow the flowables into the containers that have been added to this
        chain.

        Returns an empty iterator when all flowables have been sucessfully
        rendered.
        When the chain runs out of containers before all flowables have been
        rendered, this method returns an iterator yielding itself. This signals
        the :class:`Document` to generate a new page and register new containers
        with this chain."""
        if self._page_to_break == container.page:
            return True
        if rerender:
            container.clear()
            if not self._rerendering:
                # restore saved state on this chain's 1st container on this page
                self._state = copy(self._fresh_page_state)
                self._rerendering = True
        try:
            while self._state.flowable_index < len(self.flowables):
                flowable = self.flowables[self._state.flowable_index]
                height, last_descender \
                    = flowable.flow(container, last_descender,
                                    self._state.flowable_state)
                self._state.next_flowable()
            # all flowables have been rendered
            if container == self.last_container:
                self._init_state()    # reset state for the next rendering loop
            return False
        except EndOfContainer as e:
            self._state.flowable_state = e.flowable_state
            if e.page_break:
                self._page_to_break = container.page
                self._fresh_page_state = copy(self._state)
                return True
            if container == self.last_container:
                # save state for when ReflowRequired occurs
                self._fresh_page_state = copy(self._state)
            return container == self.last_container
        except ReflowRequired:
            self._rerendering = False
            raise
