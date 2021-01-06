# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
The layout engine. The container classes allow defining rectangular areas on a
page to which :class:`Flowable`\\ s can be rendered.

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
from .util import ContextManager


__all__ = ['Container', 'FlowablesContainer', 'ChainedContainer',
           'DownExpandingContainer', 'InlineDownExpandingContainer',
           'UpExpandingContainer', 'VirtualContainer', 'Chain',
           'FootnoteContainer', 'MaybeContainer', 'discard_state',
           'ContainerOverflow', 'EndOfContainer',
           'PageBreakException']


class ContainerOverflow(Exception):
    """The end of the :class:`FlowableContainer` has been reached."""


class EndOfContainer(Exception):
    """TODO"""

    def __init__(self, flowable_state, page_break=False):
        """`flowable_state` represents the rendering state of the
        :class:`Flowable` at the time the :class:`FlowableContainer`" overflows.
        """
        self.flowable_state = flowable_state
        self.page_break = page_break


class PageBreakException(ContainerOverflow):
    def __init__(self, break_type, chain, flowable_state):
        super().__init__()
        self.break_type = break_type
        self.chain = chain
        self.flowable_state = flowable_state


class ReflowRequired(Exception):
    """Reflow of the current page is required due to insertion of a float."""


class FlowableTarget(object):
    """Something that takes :class:`Flowable`\\ s to be rendered."""

    def __init__(self, document_part, *args, **kwargs):
        """Initialize this flowable target.

        `document_part` is the :class:`Document` this flowable target is part
        of."""
        from .flowable import StaticGroupedFlowables

        self.flowables = StaticGroupedFlowables([])
        super().__init__(*args, **kwargs)

    @property
    def document(self):
        return self.document_part.document

    def append_flowable(self, flowable):
        """Append a `flowable` to the list of flowables to be rendered."""
        self.flowables.append(flowable)

    def __lshift__(self, flowable):
        """Shorthand for :meth:`append_flowable`. Returns `self` so that it can
        be chained."""
        self.append_flowable(flowable)
        return self

    def prepare(self, document):
        self.flowables.prepare(self)



class Container(object):
    """Rectangular area that contains elements to be rendered to a
    :class:`Page`. A :class:`Container` has an origin (the top-left corner), a
    width and a height. It's contents are rendered relative to the container's
    position in its parent :class:`Container`."""

    register_with_parent = True

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
        if self.register_with_parent:
            self.parent.children.append(self)
        self.children = []
        self.clear()

    @property
    def document_part(self):
        return self.parent.document_part

    @property
    def document(self):
        return self.document_part.document

    @property
    def page(self):
        """The :class:`Page` this container is located on."""
        return self.parent.page

    def clear(self):
        self.empty_canvas()

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)

    def __getattr__(self, name):
        if name in ('_footnote_space', 'float_space'):
            return getattr(self.parent, name)
        raise AttributeError('{}.{}'.format(self.__class__.__name__, name))

    def empty_canvas(self):
        self.canvas = self.document.backend.Canvas()

    def render(self, type, rerender=False):
        """Render the contents of this container to its canvas.

        Note that the rendered contents need to be :meth:`place`\\ d on the
        parent container's canvas before they become visible."""
        for child in self.children:
            child.render(type, rerender)

    def check_overflow(self):
        return all(child.check_overflow() for child in self.children)

    def place_children(self):
        for child in self.children:
            child.place()

    def place(self):
        """Place this container's canvas onto the parent container's canvas."""
        self.place_children()
        self.canvas.append(self.parent.canvas,
                           float(self.left), float(self.top))

    def before_placing(self):
        for child in self.children:
            child.before_placing()


BACKGROUND = 'background'
CONTENT = 'content'
HEADER_FOOTER = 'header_footer'
CHAPTER_TITLE = 'chapter_title'


class FlowablesContainerBase(Container):
    """A :class:`Container` that renders :class:`Flowable`\\ s to a rectangular
    area on a page. The first flowable is rendered at the top of the container.
    The next flowable is rendered below the first one, and so on."""

    def __init__(self, name, type, parent, left=None, top=None,
                 width=None, height=None, right=None, bottom=None):
        self._self_cursor = Dimension(0)  # initialized at container's top edge
        self._cursor = DimensionAddition(self._self_cursor)
        self._placed_styleds = {}
        super().__init__(name, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom)
        self.type = type

    @property
    def top_level_container(self):
        try:
            return self.parent.top_level_container
        except AttributeError:
            return self

    def clear(self):
        super().clear()
        del self.children[:]
        self._placed_styleds.clear()
        self._self_cursor._value = 0  # initialized at container's top edge
        del self._cursor.addends[1:]

    def mark_page_nonempty(self):
        if self.type == CONTENT:
            self.page._empty = False
        elif self.type is None:
            self.parent.mark_page_nonempty()

    @property
    def cursor(self):
        """Keeps track of where the next flowable is to be placed. As flowables
        are flowed into the container, the cursor moves down."""
        return float(self._cursor)

    @property
    def remaining_height(self):
        return self.height - self.cursor

    def advance(self, height, ignore_overflow=False):
        """Advance the cursor by `height`. If this would cause the cursor to
        point beyond the bottom of the container, an :class:`EndOfContainer`
        exception is raised."""
        if height <= self.remaining_height:
            self._self_cursor.grow(height)
        elif ignore_overflow:
            self._self_cursor.grow(float(self.remaining_height))
        else:
            raise ContainerOverflow(self.page.number)

    def advance2(self, height, ignore_overflow=False):
        """Advance the cursor by `height`. Returns `True` on success.

        Returns `False` if this would cause the cursor to point beyond the
        bottom of the container.

        """
        if height <= self.remaining_height:
            self._self_cursor.grow(height)
        elif ignore_overflow:
            self._self_cursor.grow(float(self.remaining_height))
        else:
            return False
        return True

    def check_overflow(self):
        return self.remaining_height > 0

    def render(self, type, rerender=False):
        if type in (self.type, None):
            self._render(type, rerender)

    def _render(self, type, rerender):
        raise NotImplementedError('{}.render()'.format(self.__class__.__name__))

    def register_styled(self, styled, continued=False):
        styleds = self._placed_styleds.setdefault(len(self.children), [])
        styleds.append((styled, continued))

    def before_placing(self):
        def log_styleds(index):
            for styled, continued in self._placed_styleds.get(index, ()):
                self.document.style_log.log_styled(styled, self, continued)
                styled.before_placing(self)

        log_styleds(0)
        for i, child in enumerate(self.children, start=1):
            child.before_placing()
            log_styleds(i)


class _FlowablesContainer(FlowableTarget, FlowablesContainerBase):
    def __init__(self, name, type, parent, *args, **kwargs):
        super().__init__(parent.document_part, name, type, parent,
                         *args, **kwargs)

    def _render(self, type, rerender):
        self.flowables.flow(self, last_descender=None)


class FlowablesContainer(_FlowablesContainer):
    """A container that renders a predefined series of flowables."""

    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 height=None, right=None, bottom=None):
        super().__init__(name, type, parent, left=left, top=top,
                         width=width, height=height, right=right, bottom=bottom)



class ChainedContainer(FlowablesContainerBase):
    """A container that renders flowables from the :class:`Chain` it is part
    of."""

    def __init__(self, name, type, parent, chain, left=None, top=None,
                 width=None, height=None, right=None, bottom=None):
        super().__init__(name, type, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom)
        chain.containers.append(self)
        self.chain = chain

    def _render(self, type, rerender):
        self.chain.render(self, rerender=rerender)


class ExpandingContainerBase(FlowablesContainerBase):
    """A dynamically, vertically growing :class:`Container`."""

    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 right=None, bottom=None, max_height=None):
        """See :class:`ContainerBase` for information on the `parent`, `left`,
        `width` and `right` parameters.

        `max_height` is the maximum height this container can grow to."""
        height = DimensionAddition()
        super().__init__(name, type, parent, left=left, top=top,
                         width=width, height=height, right=right, bottom=bottom)
        self.height.addends.append(self._cursor)
        self.max_height = max_height or float('+inf')

    @property
    def remaining_height(self):
        return self.max_height - self.cursor


class DownExpandingContainerBase(ExpandingContainerBase):
    """A container that is anchored at the top and expands downwards."""

    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 right=None, max_height=None):
        """See :class:`Container` for information on the `name`, `parent`,
        `left`, `width` and `right` parameters.

        `top` specifies the location of the container's top edge with respect to
        that of the parent container. When `top` is omitted, the top edge is
        placed at the top edge of the parent container.

        `max_height` is the maximum height this container can grow to."""
        super().__init__(name, type, parent, left=left, top=top, width=width,
                         right=right, max_height=max_height)


class DownExpandingContainer(_FlowablesContainer, ExpandingContainerBase):
    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 right=None, max_height=None):
        super().__init__(name, type, parent, left=left, top=top,
                         width=width, right=right, max_height=max_height)


class ConditionalDownExpandingContainerBase(DownExpandingContainerBase):
    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 right=None, max_height=None, place=True):
        super().__init__(name, type, parent, left=left, top=top, width=width,
                         right=right, max_height=max_height)
        self._do_place = place

    def do_place(self, place=True):
        self._do_place = place

    def place(self):
        if self._do_place:
            super().place()

    def before_placing(self):
        if self._do_place:
            super().before_placing()


class InlineDownExpandingContainer(ConditionalDownExpandingContainerBase):
    """A :class:`DownExpandingContainer` whose top edge is placed at the
    parent's current cursor position. As flowables are flowed in this container,
    the parent's cursor also advances (but this behavior can be suppressed).

    See :class:`Container` about the `name`, `parent`, `left`, `width`
    and `right` parameters. Setting `advance_parent` to `False` prevents the
    parent container's cursor being advanced.

    """

    def __init__(self, name, parent, left=None, width=None, right=None,
                 advance_parent=True, place=True):
        super().__init__(name, None, parent, left=left, top=parent.cursor,
                         width=width, right=right,
                         max_height=parent.remaining_height, place=place)
        if advance_parent:
            parent._cursor.addends.append(self._cursor)


class UpExpandingContainer(_FlowablesContainer, ExpandingContainerBase):
    """A container that is anchored at the bottom and expands upwards."""

    def __init__(self, name, type, parent, left=None, bottom=None, width=None,
                 right=None, max_height=None):
        """See :class:`ContainerBase` for information on the `name`, `parent`,
        `left`, `width` and `right` parameters.

        `bottom` specifies the location of the container's bottom edge with
        respect to that of the parent container. When `bottom` is omitted, the
        bottom edge is placed at the bottom edge of the parent container.

        `max_height` is the maximum height this container can grow to."""
        bottom = bottom or parent.height
        super().__init__(name, type, parent, left=left, top=None, width=width,
                         right=right, bottom=bottom, max_height=max_height)


class _MaybeContainer(InlineDownExpandingContainer):
    def __init__(self, parent, left=None, width=None, right=None):
        super().__init__('MAYBE', parent, left=left, width=width, right=right,
                         place=False)


class MaybeContainer(ContextManager):
    def __init__(self, parent, left=None, width=None, right=None):
        self._container = _MaybeContainer(parent, left, width, right)

    def __enter__(self):
        return self._container

    def __exit__(self, exc_type, exc_value, _):
        if (exc_type is None or (issubclass(exc_type, (EndOfContainer,
                                                       PageBreakException))
                                 and not exc_value.flowable_state.initial)):
            self._container.do_place()


@contextmanager
def discard_state(initial_state):
    saved_state = copy(initial_state)
    try:
        yield
    except EndOfContainer:
        raise EndOfContainer(saved_state)


class VirtualContainer(ConditionalDownExpandingContainerBase):
    """An infinitely down-expanding container whose contents are not
    automatically placed on the parent container's canvas. This container's
    content needs to be placed explicitly using :meth:`place_at`."""

    register_with_parent = False

    def __init__(self, parent, width=None):
        """`width` specifies the width of the container."""
        super().__init__('VIRTUAL', None, parent, width=width,
                         max_height=float('+inf'), place=False)

    def place_at(self, parent_container, left, top):
        self.parent = parent_container
        parent_container.children.append(self)
        self.left = left
        self.top = top
        self.do_place()


class FloatContainer(ExpandingContainerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TopFloatContainer(DownExpandingContainer, FloatContainer):
    pass


class BottomFloatContainer(UpExpandingContainer, FloatContainer):
    pass


class FootnoteContainer(UpExpandingContainer):
    def __init__(self, name, parent, left=None, bottom=None, width=None,
                 right=None, max_height=None):
        super().__init__(name, CONTENT, parent, left, bottom,
                         width=width, right=right, max_height=max_height)
        self._footnote_number = 0
        self._footnote_space = self
        self.footnote_queue = deque()
        self._flowing_footnotes = False
        self._reflowed = False
        self._descenders = [0]

    def add_footnote(self, footnote):
        self.footnote_queue.append(footnote)
        if not self._flowing_footnotes:
            self._flowing_footnotes = True
            if not self.flow_footnotes():
                return False
            self._flowing_footnotes = False
        return True

    def flow_footnotes(self):
        if self._reflowed:
            self._cursor.addends.pop()
            self._descenders.pop()
        maybe_container = _MaybeContainer(self)
        while self.footnote_queue:
            footnote = self.footnote_queue.popleft()
            footnote_id = footnote.get_id(self.document)
            if footnote_id not in self.document.placed_footnotes:
                _, _, descender = footnote.flow(maybe_container,
                                                self._descenders[-1])
                self._descenders.append(descender)
                self._reflowed = True
                if not self.page.check_overflow():
                    return False
                self._reflowed = False
                self.document.placed_footnotes.add(footnote_id)
        maybe_container.do_place()
        return True

    @property
    def next_number(self):
        self._footnote_number += 1
        return self._footnote_number


class Chain(FlowableTarget):
    """A :class:`FlowableTarget` that renders its flowables to a series of
    containers. Once a container is filled, the chain starts flowing flowables
    into the next container."""

    def __init__(self, document_part):
        """Initialize this chain.

        `document` is the :class:`Document` this chain is part of."""
        super().__init__(document_part)
        self.document_part = document_part
        self._init_state()
        self.containers = []
        self.done = True

    def _init_state(self):
        """Reset the state of this chain: empty the list of containers, and zero
        the counter keeping track of which flowable needs to be rendered next.
        """
        self._state = self._fresh_page_state = None
        self._rerendering = False

    @property
    def last_container(self):
        return self.containers[-1]

    def render(self, container, rerender=False):
        """Flow the flowables into the containers that have been added to this
        chain."""
        if rerender:
            container.clear()
            if not self._rerendering:
                # restore saved state on this chain's 1st container on this page
                self._state = copy(self._fresh_page_state)
                self._rerendering = True
        try:
            self.done = False
            self.flowables.flow(container, last_descender=None,
                                state=self._state)
            # all flowables have been rendered
            from .flowable import GroupedFlowablesState
            self._state = GroupedFlowablesState(None, [])
            if container == self.last_container:
                self._init_state()    # reset state for the next rendering loop
            self.done = True
        except PageBreakException as exc:
            self._state = exc.flowable_state
            self._fresh_page_state = copy(self._state)
            raise
        except EndOfContainer as e:
            self._state = e.flowable_state
            if container == self.last_container:
                # save state for when ReflowRequired occurs
                self._fresh_page_state = copy(self._state)
        except ReflowRequired:
            self._rerendering = False
            raise
