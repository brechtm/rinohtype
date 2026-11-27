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
* :exc:`EndOfContainer`: Exception raised when a container "overflows" during
                         the rendering of flowables.
* :class:`Chain`: A chain of containers. When a container overflows, the
                  rendering of the chain's flowables is continued in the next
                  container in the chain.
* :class:`FootnoteContainer`: TODO

"""

from collections import deque
from contextlib import contextmanager
from copy import copy
from functools import cached_property

from .annotation import AnnotationTransform
from .dimension import DimensionBase, DimensionScope, PT
from .util import ContextManager


__all__ = ['Container', 'FlowablesContainer', 'ChainedContainer',
           'DownExpandingContainer', 'InlineDownExpandingContainer',
           'UpExpandingContainer', 'UpDownExpandingContainer',
           'VirtualContainer', 'Chain', 'FootnoteContainer', 'MaybeContainer',
           'FlowContext', 'PageGeometry', 'ContainerOverflow',
           'EndOfContainer', 'PageBreakException']


#: annotation transform at the page level; maps coordinates onto themselves
IDENTITY = AnnotationTransform()


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



class FlowContext(object):
    """The layout context a container subtree is rendered in.

    A context is shared by reference between a container and all its
    descendants. Values that are derived from the container hierarchy are
    looked up in the context, so they never need to be cached per container
    nor invalidated when a container is re-parented: a re-parented container
    keeps referencing the same context, which is shared by its new ancestors
    as well.

    Attributes:
        page (Page): the page the subtree is located on
        top_level_container (FlowablesContainerBase): the top-level container
            the subtree is rendered in
        never_placed (bool): whether the subtree is only being measured and
            its contents should not be drawn
    """

    __slots__ = ('page', 'top_level_container', 'never_placed')

    def __init__(self, page, top_level_container, never_placed=False):
        self.page = page
        self.top_level_container = top_level_container
        self.never_placed = never_placed

    def inside(self, container):
        """The context for the contents of `container`, which is a new
        top-level container"""
        return FlowContext(self.page, container, self.never_placed)

    def measuring(self):
        """The context for a subtree that only lays out its contents to
        measure them"""
        return FlowContext(self.page, self.top_level_container, True)


class ContainerBase(object):
    """Rectangular area that contains elements to be rendered to a
    :class:`Page`. A container has an origin (the top-left corner), a width
    and a height. Its contents are rendered relative to the container's
    position in its parent container."""

    register_with_parent = True

    def __init__(self, name, parent, left=None, top=None, width=None,
                 height=None, right=None, bottom=None):
        """Initialize this container as a child of the `parent` container.

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

        if top is None:
            top = 0*PT if (bottom and height) is None else (bottom - height)
        if height is None:
            height = (parent.height - top) if bottom is None else (bottom - top)
        if bottom is None:
            bottom = top + height

        self.left = left
        self.width = width
        self.right = right
        self.top = top
        self.height = height
        self.bottom = bottom

        self.name = name
        self.parent = parent
        if parent is not None:      # a Page sets up its own context
            self.context = parent.context
        if self.register_with_parent:
            self.parent.children.append(self)
        self.children = []

    @property
    def document_part(self):
        return self.context.page.document_part

    @cached_property
    def document(self):
        return self.parent.document

    @property
    def never_placed(self):
        return self.context.never_placed

    @property
    def page(self):
        """The :class:`Page` this container is located on."""
        return self.context.page

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)

    def __getattr__(self, name):
        # the footnote and float spaces are attributes of the page; looking
        # them up there avoids walking up the container hierarchy
        if name in ('footnote_space', 'float_space'):
            try:
                # object.__getattribute__ does not fall back to __getattr__
                # (which would recurse when the page is this container)
                return object.__getattribute__(self.context.page, name)
            except AttributeError:
                pass
        raise AttributeError('{}.{}'.format(self.__class__.__name__, name))

    def render(self, type, rerender=False):
        """Render the contents of this container to its canvas.

        Note that the rendered contents need to be :meth:`place`\ d on the
        parent container's canvas before they become visible."""
        self._resolve_geometry()
        for child in self.children:
            child.render(type, rerender)

    def _resolve_geometry(self):
        """Bring the page template's geometry up to date, if needed

        A container's edges are stored as plain floats on the page's template
        containers. They are re-evaluated only when a container they depend on
        has changed (see :class:`PageGeometry`)."""
        geometry = getattr(self.context.page, '_geometry', None)
        if geometry is not None:
            geometry.resolve()

    def check_overflow(self):
        return all(child.check_overflow() for child in self.children)

    def place_children(self, page_canvas, annotation_transform=IDENTITY):
        for child in self.children:
            child._resolve_geometry()
            child.place(page_canvas, annotation_transform)

    def before_placing(self, preallocate=False):
        for child in self.children:
            child._resolve_geometry()
            child.before_placing(preallocate)


class Container(ContainerBase):
    """A container whose contents are rendered to an intermediate canvas,
    which is written to the page's canvas when the container is placed."""

    def __init__(self, name, parent, left=None, top=None, width=None,
                 height=None, right=None, bottom=None, sideways=None):
        """Initialize this container as a child of the `parent` container.

        See :class:`ContainerBase` about the `name`, `parent`, `left`, `top`,
        `width`, `height`, `right` and `bottom` parameters.

        `sideways` rotates the contents of this container on the page."""
        if sideways:
            width, height = height, width
        super().__init__(name, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom)
        self.sideways = sideways
        self.clear()

    def clear(self):
        self.empty_canvas()

    def empty_canvas(self):
        self._canvas = None

    @property
    def canvas(self):
        """The canvas to draw this container's contents on; created only when
        something is drawn"""
        if self._canvas is None:
            self._canvas = self.document.backend.Canvas()
        return self._canvas

    def place(self, page_canvas, annotation_transform=IDENTITY):
        """Write this container's contents onto the page's canvas

        The contents are written directly to `page_canvas` instead of to the
        parent container's canvas, so that they are copied only once.

        Args:
            page_canvas (Canvas): the canvas of the page
            annotation_transform (AnnotationTransform): maps this container's
                annotation coordinates to those of the page (identity at the
                page level)

        """
        left, top = float(self.left), float(self.top)
        annotation_transform = annotation_transform.compose(
            page_canvas.annotation_transform(left, top, self.width,
                                             self.height, self.sideways))
        with page_canvas.save_state():
            page_canvas.translate(left, top)
            if self.sideways == 'left':
                page_canvas.translate(float(self.height), 0)
                page_canvas.rotate(-90)
            elif self.sideways == 'right':
                page_canvas.translate(0, float(self.width))
                page_canvas.rotate(90)
            if self._canvas is not None:
                # contents drawn directly on this container are subject to
                # the sideways transform as well
                self._canvas.write_to(page_canvas, annotation_transform)
                self._canvas = None     # no longer needed
            self.place_children(page_canvas, annotation_transform)


BACKGROUND = 'background'
CONTENT = 'content'
HEADER_FOOTER = 'header_footer'
CHAPTER_TITLE = 'chapter_title'


class PageGeometry(object):
    """The geometry of a page template's containers, evaluated to floats

    A page template wires its containers together with late-evaluated
    :class:`Dimension`\\ s. For example, the bottom edge of the body text
    columns coincides with the top edge of the footnote space. Evaluating
    those dimensions on every lookup is expensive, so they are evaluated once
    here and written to the containers as plain floats.

    Only the height of the expanding containers defined by the page template
    (the footnote space, the float space and an expanding chapter title) can
    change while a page is laid out. Such a container is marked as a geometry
    source; growing or clearing it marks the geometry as changed, and it is
    re-evaluated before a container is rendered or placed, and after a
    footnote or float was added:

    * :meth:`ContainerBase.render` and :meth:`ContainerBase.place_children`
      (before rendering or placing a container)
    * :meth:`Page.check_overflow` (after a footnote or float was added)
    * :meth:`Page.render` and :meth:`Page.place`
    * :meth:`NewChapterBodyPage.create_chapter_title` (after flowing it)

    The mutation sites and the invalidation are therefore explicit and local
    to the page. ``version`` is bumped on every resolution, so that the flow
    containers that derive their limit from another container know when to
    re-evaluate it.

    """

    EDGES = ('left', 'top', 'width', 'height', 'right', 'bottom')

    def __init__(self, page):
        self.page = page
        self._containers = []
        self._scope = DimensionScope()
        self._dirty = True
        self.version = 0    # bumped each time the geometry is resolved

    def setup(self):
        """Register the page template's containers and cache their edges"""
        for container in self._descendants(self.page):
            self._containers.append(container)
            if isinstance(container, ExpandingContainerBase):
                # its height can change while the page is laid out
                container._geometry_source = True
            for edge in self.EDGES:
                dimension = getattr(container, edge)
                if (edge == 'top'
                        and getattr(container, 'vertically_center_content',
                                    False)):
                    dimension = dimension + _VerticalOffset(container)
                setattr(container, edge, self._scope.cached(dimension))
        self.resolve()

    @classmethod
    def _descendants(cls, container):
        for child in container.children:
            yield child
            yield from cls._descendants(child)

    def resolve(self):
        """Update the cached dimensions if a geometry source has changed

        Does nothing if no geometry-changing container has changed since the
        last resolution."""
        if not self._dirty:
            return
        self._scope.changed()
        for container in self._containers:
            if (isinstance(container, FlowablesContainerBase)
                    and not container._expanding):
                container._limit = float(container.height)
        self.version += 1
        self._dirty = False

    def mark_changed(self):
        """Note that a container the template geometry depends on changed"""
        self._dirty = True

    def update(self):
        """Resolve the geometry, which is known to have changed"""
        self._dirty = True
        self.resolve()


class _VerticalOffset(DimensionBase):
    """The offset applied to a vertically centered container's top edge"""

    def __init__(self, container):
        self.container = container

    def __float__(self):
        return self.container._vertical_offset


class FlowablesContainerBase(Container):
    """A :class:`Container` that renders :class:`Flowable`\\ s to a rectangular
    area on a page. The first flowable is rendered at the top of the container.
    The next flowable is rendered below the first one, and so on."""

    #: whether this container's height follows from its cursor
    _expanding = False

    #: whether this container is part of the page template's geometry
    _geometry_source = False

    #: the container that includes this container's cursor in its own
    _advance_parent = None

    def __init__(self, name, type, parent, left=None, top=None,
                 width=None, height=None, right=None, bottom=None,
                 vertically_center_content=False):
        self._cursor = 0.0      # this container's own advance
        self._child = None      # sub-container currently advancing this one
        self._limit = float('+inf')     # height the cursor can advance to
        self._vertical_offset = 0.0     # offset applied by vertical centering
        self._placed_styleds = {}
        super().__init__(name, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom)
        if not isinstance(parent, FlowablesContainerBase):
            self.context = self.context.inside(self)
        if not self._expanding:
            self._limit = float(self.height)
        self.type = type
        self.vertically_center_content = vertically_center_content

    @property
    def top_level_container(self):
        return self.context.top_level_container

    def clear(self):
        super().clear()
        del self.children[:]
        self._placed_styleds.clear()
        self._cursor = 0.0      # reset to the container's top edge
        self._child = None
        if self._geometry_source:
            self.context.page.geometry.mark_changed()

    def mark_page_nonempty(self):
        context = self.context
        if context.top_level_container.type is CONTENT:
            context.page._empty = False

    @property
    def cursor(self):
        """Keeps track of where the next flowable is to be placed. As flowables
        are flowed into the container, the cursor moves down."""
        child = self._child
        return self._cursor if child is None else self._cursor + child.cursor

    @property
    def remaining_height(self):
        child = self._child
        cursor = self._cursor if child is None else self._cursor + child.cursor
        return self._limit - cursor

    def _fold(self):
        """Move the advance of the sub-container flowing into this container
        into this container's own cursor"""
        child = self._child
        if child is not None:
            self._cursor += child.cursor
            self._child = None
            if child._advance_parent is self:
                child._advance_parent = None

    def _adopt(self, child):
        """Include `child`'s cursor in this container's cursor"""
        self._fold()
        self._child = child
        child._advance_parent = self

    def _discard(self, child):
        """Undo :meth:`_adopt`: `child`'s advance no longer counts"""
        if self._child is child:
            self._child = None
        if child._advance_parent is self:
            child._advance_parent = None

    def _abandon(self):
        """Stop advancing the container this container was advancing"""
        parent = self._advance_parent
        if parent is not None:
            parent._discard(self)

    def _advance(self, height, ignore_overflow):
        """Move the cursor down by `height`, if it fits. Returns whether it
        did (or was clamped with `ignore_overflow`)."""
        height = float(height)
        child = self._child
        cursor = self._cursor if child is None else self._cursor + child.cursor
        remaining_height = self._limit - cursor
        if height > remaining_height + FLOATING_POINT_FUZZ:
            if not ignore_overflow:
                return False
            height = remaining_height
        self._fold()
        self._cursor += height
        if self._geometry_source and height:
            self.context.page.geometry.mark_changed()
        return True

    def advance(self, height, ignore_overflow=False):
        """Advance the cursor by `height`. If this would cause the cursor to
        point beyond the bottom of the container, a :class:`ContainerOverflow`
        exception is raised."""
        if not self._advance(height, ignore_overflow):
            raise ContainerOverflow(self.page.number)

    def advance2(self, height, ignore_overflow=False):
        """Advance the cursor by `height`. Returns `True` on success.

        Returns `False` if this would cause the cursor to point beyond the
        bottom of the container.

        """
        return self._advance(height, ignore_overflow)

    def check_overflow(self):
        return self.type is not CONTENT or self.remaining_height > 0

    def render(self, type, rerender=False):
        self._resolve_geometry()
        if type in (self.type, None):
            self._render(type, rerender)
        if self.vertically_center_content and type is CONTENT:
            self._vertical_offset = float(self.remaining_height) / 2
            self.context.page.geometry.mark_changed()
        if self._geometry_source:
            self.context.page.geometry.mark_changed()

    def _render(self, type, rerender):
        raise NotImplementedError('{}.render()'.format(self.__class__.__name__))

    def register_styled(self, styled, continued=False):
        self.registered_styleds().append((styled, continued))

    def registered_styleds(self):
        """The styled elements registered at the current position"""
        return self._placed_styleds.setdefault(len(self.children), [])

    def before_placing(self, preallocate=False):
        def log_styleds(index):
            for styled, continued in self._placed_styleds.get(index, ()):
                self.document.style_log.log_styled(styled, self, continued)
                styled.before_placing(self, preallocate)

        log_styleds(0)
        for i, child in enumerate(self.children, start=1):
            child.before_placing(preallocate)
            log_styleds(i)


FLOATING_POINT_FUZZ = 1e-10


class _FlowablesContainer(FlowableTarget, FlowablesContainerBase):
    def __init__(self, name, type, parent, *args, **kwargs):
        super().__init__(parent.document_part, name, type, parent,
                         *args, **kwargs)

    def _render(self, type, rerender):
        self.flowables.flow(self, last_descender=None)


class FlowablesContainer(_FlowablesContainer):
    """A container that renders a predefined series of flowables."""

    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 height=None, right=None, bottom=None,
                 vertically_center_content=False):
        super().__init__(name, type, parent, left=left, top=top,
                         width=width, height=height, right=right, bottom=bottom,
                         vertically_center_content=vertically_center_content)


class ChainedContainer(FlowablesContainerBase):
    """A container that renders flowables from the :class:`Chain` it is part
    of."""

    def __init__(self, name, type, parent, chain, left=None, top=None,
                 width=None, height=None, right=None, bottom=None,
                 vertically_center_content=False):
        super().__init__(name, type, parent, left=left, top=top, width=width,
                         height=height, right=right, bottom=bottom,
                         vertically_center_content=vertically_center_content)
        chain.containers.append(self)
        self.chain = chain

    def _render(self, type, rerender):
        self.chain.render(self, rerender=rerender)


class ContainerHeight(DimensionBase):
    """The height of an expanding container: its (live) cursor position"""

    def __init__(self, container):
        self.container = container

    def __float__(self):
        return self.container.cursor


class ExpandingContainerBase(FlowablesContainerBase):
    """A dynamically, vertically growing :class:`Container`."""

    _expanding = True

    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 right=None, bottom=None, max_height=None):
        """See :class:`ContainerBase` for information on the `parent`, `left`,
        `width` and `right` parameters.

        `max_height` is the maximum height this container can grow to."""
        super().__init__(name, type, parent, left=left, top=top, width=width,
                         height=ContainerHeight(self), right=right,
                         bottom=bottom)
        self._limit = (float('+inf') if max_height is None
                       else float(max_height))


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
    """Expanding container used while flowing flowables, as opposed to the
    containers defined by page templates

    Its horizontal geometry is evaluated on creation. Growing it does not
    affect the geometry of any template-defined container, except through the
    containers it advances."""

    _expanding = False
    sideways = None
    vertically_center_content = False

    def __init__(self, name, type, parent, left=None, top=None, width=None,
                 right=None, max_height=None, place=True):
        # many of these are created while flowing; so instead of going through
        # the base classes' __init__, initialize all attributes directly
        if left is None:
            left = 0.0 if (right and width) is None else right - width
        left = float(left)
        if width is None:
            width = (float(parent.width) if right is None
                     else float(right)) - left
        else:
            width = float(width)
        self.left = left
        self.width = width
        self.right = left + width if right is None else float(right)
        self.top = 0.0 if top is None else float(top)
        self.name = name
        self.parent = parent
        if isinstance(parent, FlowablesContainerBase):
            self.context = parent.context
        else:
            self.context = parent.context.inside(self)
        self.document = parent.document
        if self.register_with_parent:
            parent.children.append(self)
        self.children = []
        self._canvas = None
        self._cursor = 0.0
        self._child = None
        self._advance_parent = None
        self._base_limit = (float('+inf') if max_height is None
                            else float(max_height))
        self._placed_styleds = {}
        self.type = type
        self._do_place = place

    @property
    def _limit(self):
        return self._base_limit

    @property
    def height(self):
        return self.cursor

    @property
    def bottom(self):
        return self.top + self.height

    def do_place(self, place=True):
        self._do_place = place

    def place(self, page_canvas, annotation_transform=IDENTITY):
        if self._do_place:
            super().place(page_canvas, annotation_transform)

    def before_placing(self, preallocate=False):
        if self._do_place:
            super().before_placing(preallocate)


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
                         width=width, right=right, place=place)
        self._limit_parent = parent
        self._limit_offset = parent.cursor
        self._limit_version = None
        self._cached_limit = 0.0
        context = getattr(parent, 'context', None)
        page = None if context is None else context.page
        self._geometry = getattr(page, '_geometry', None)
        if advance_parent:
            parent._adopt(self)

    @property
    def _limit(self):
        # the parent's remaining height at the time this container was created,
        # re-evaluated whenever the page template's geometry was resolved
        geometry = self._geometry
        if geometry is None:
            return self._limit_parent._limit - self._limit_offset
        if geometry.version != self._limit_version:
            self._cached_limit = self._limit_parent._limit - self._limit_offset
            self._limit_version = geometry.version
        return self._cached_limit


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


class UpDownExpandingContainer(_FlowablesContainer, ExpandingContainerBase):
    """A container that is anchored in the middle and symetrically expands
    upwards and downwards."""

    def __init__(self, name, type, parent, left=None, middle=None, width=None,
                 right=None, max_height=None):
        """See :class:`ContainerBase` for information on the `name`, `parent`,
        `left`, `width` and `right` parameters.

        `middle` specifies the location of the container's vertical center with
        respect to the top of the parent container. When `middle` is omitted,
        the middle is placed at the top edge of the parent container.

        `max_height` is the maximum height this container can grow to."""
        if middle is None:
            middle = 0*PT
        top = middle
        super().__init__(name, type, parent, left=left, top=top, width=width,
                         right=right, max_height=max_height)
        self.top -= self.height / 2


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
        container = self._container
        if (exc_type is None
                or (issubclass(exc_type, (EndOfContainer, PageBreakException))
                    and not exc_value.flowable_state.initial)):
            container.do_place()
        else:
            # nothing of what was flowed can be used; undo the advance
            container._abandon()


class VirtualContainer(ConditionalDownExpandingContainerBase):
    """An infinitely down-expanding container whose contents are not
    automatically placed on the parent container's canvas. This container's
    content needs to be placed explicitly using :meth:`place_at`."""

    register_with_parent = False

    def __init__(self, parent, width=None, never_placed=False):
        """`width` specifies the width of the container."""
        super().__init__('VIRTUAL', None, parent, width=width,
                         max_height=float('+inf'), place=False)
        if never_placed and not self.context.never_placed:
            self.context = self.context.measuring()

    def place_at(self, parent_container, left, top):
        # The new parent is the tentative parent or an ancestor of it, so both
        # share this container's context and page, top_level_container and
        # never_placed remain valid.
        assert parent_container.context is self.context
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
        self.footnote_space = self
        self.footnotes = []
        self._flowing_footnotes = False
        self._reflowed = False
        self._descenders = [0]
        self._allocation_phase = True
        self._placed_footnotes = set()
        parent.footnote_space = self

    def add_footnote(self, footnote, preallocate):
        self.footnotes.append(footnote)
        if not self._flowing_footnotes:
            self._flowing_footnotes = True
            if not self.flow_footnotes(preallocate):
                return False
            self._flowing_footnotes = False
        return True

    def flow_footnotes(self, preallocate=False):
        if self._allocation_phase and not preallocate:
            self.clear()
            self._descenders = [0]
            self._allocation_phase = False
            self._placed_footnotes.clear()
        if self._reflowed:      # discard the footnotes flowed last time
            self._discard(self._footnotes_container)
            self._descenders.pop()
        maybe_container = self._footnotes_container = _MaybeContainer(self)
        for i, footnote in enumerate(self.footnotes):
            footnote_id = footnote.get_id(self.document)
            if footnote_id not in (self._placed_footnotes
                                   | self.document.placed_footnotes):
                _, _, descender = footnote.flow(maybe_container,
                                                self._descenders[-1],
                                                footnote=True)
                self._descenders.append(descender)
                self._reflowed = True
                if not self.page.check_overflow():
                    assert self._allocation_phase
                    return False
                self._reflowed = False
                self._placed_footnotes.add(footnote_id)
        if not self._allocation_phase:
            self.document.placed_footnotes |= self._placed_footnotes
            maybe_container.do_place()
        return True


class Chain(FlowableTarget):
    """A :class:`FlowableTarget` that renders its flowables to a series of
    containers. Once a container is filled, the chain starts flowing flowables
    into the next container."""

    def __init__(self, document_part):
        """Initialize this chain.

        `document` is the :class:`Document` this chain is part of."""
        super().__init__(document_part)
        self.document_part = document_part
        self.init_state()
        self.containers = []
        self.done = True

    def init_state(self):
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
