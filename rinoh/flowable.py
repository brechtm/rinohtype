# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Base classes for flowable and floating document elements. These are elements
that make up the content of a document and are rendered onto its pages.

* :class:`Flowable`: Element that is rendered onto a :class:`Container`.
* :class:`FlowableStyle`: Style class specifying the vertical space surrounding
                          a :class:`Flowable`.
* :class:`Floating`: Decorator to transform a :class:`Flowable` into a floating
                     element.
"""


from copy import copy
from itertools import chain, tee

from .layout import EndOfContainer, DownExpandingContainer, MaybeContainer
from .style import Style, Styled
from .util import Decorator


__all__ = ['Flowable', 'FlowableStyle', 'Floating']


class FlowableException(Exception):
    def __init__(self, flowable):
        self.flowable = flowable


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


class FlowableState(object):
    """Stores a :class:`Flowable`\'s rendering state, which can be copied. This
    enables saving the rendering state at certain points in the rendering
    process, so rendering can later be resumed at those points, if needed."""

    def __copy__(self):
        raise NotImplementedError


class Flowable(Styled):
    """An element that can be 'flowed' into a :class:`Container`. A flowable can
    adapt to the width of the container, or it can horizontally align itself in
    the container."""

    style_class = FlowableStyle

    def __init__(self, style=None, parent=None):
        """Initialize this flowable and associate it with the given `style` and
        `parent` (see :class:`Styled`)."""
        super().__init__(style=style, parent=parent)

    def flow(self, container, last_descender, state=None):
        """Flow this flowable into `container` and return the vertical space
        consumed.

        The flowable's contents is preceded by a vertical space with a height
        as specified in its style's `space_above` attribute. Similarly, the
        flowed content is followed by a vertical space with a height given
        by the `space_below` style attribute."""
        start_offset = container.cursor
        document = container.document
        if not state:
            container.advance(float(self.get_style('space_above', document)))
        left = self.get_style('indent_left', document)
        right = container.width - self.get_style('indent_right', document)
        max_height = container.remaining_height
        pad_container = DownExpandingContainer('PADDED',
                                               container,
                                               top=container.cursor,
                                               left=left, right=right,
                                               max_height=max_height)
        last_descender = self.render(pad_container, last_descender, state=state)
        container.advance(pad_container.cursor)
        try:
            container.advance(float(self.get_style('space_below', document)))
        except EndOfContainer:
            pass
        return container.cursor - start_offset, last_descender

    def spans(self):
        yield self

    def split(self):
        yield

    @property
    def font(self):
        """Raises :class:`FlowableException`.
        (accessed when this flowable is embedded in a paragraph)"""
        raise FlowableException(self)

    def render(self, container, descender, state=None):
        """Renders the flowable's content to `container`, with the flowable's
        top edge lining up with the container's cursor. `descender` is the
        descender height of the preceeding line or `None`."""
        raise NotImplementedError


class InseparableFlowables(Flowable):
    def __init__(self, flowables, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.flowables = flowables

    def render(self, container, last_descender, state=None):
        maybe_container = MaybeContainer(container)
        for flowable in self.flowables:
            _, last_descender = flowable.flow(maybe_container, last_descender)
        maybe_container.do_place()
        return last_descender


class GroupedFlowablesState(FlowableState):
    def __init__(self, flowables, first_flowable_state=None):
        self.flowables = flowables
        self.first_flowable_state = first_flowable_state

    def __copy__(self):
        copy_list_items, self.flowables = tee(self.flowables)
        copy_first_flowable_state = copy(self.first_flowable_state)
        return self.__class__(copy_list_items, copy_first_flowable_state)

    def next_flowable(self):
        return next(self.flowables)

    def prepend(self, flowable, first_flowable_state):
        self.flowables = chain((flowable, ), self.flowables)
        self.first_flowable_state = first_flowable_state


class GroupedFlowables(Flowable, list):
    def render(self, container, descender, state=None):
        state = state or GroupedFlowablesState(iter(self), None)

        try:
            while True:
                flowable = state.next_flowable()
                _, descender = flowable.flow(container, descender,
                                             state=state.first_flowable_state)
                state.first_flowable_state = None
        except EndOfContainer as eoc:
            state.prepend(flowable, eoc.flowable_state)
            raise EndOfContainer(state)
        except StopIteration:
            pass


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
