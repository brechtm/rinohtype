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
from itertools import chain, takewhile, tee

from .annotation import NamedDestination
from .dimension import PT
from .draw import ShapeStyle, Rectangle, Line, LineStyle
from .layout import (InlineDownExpandingContainer, VirtualContainer,
                     MaybeContainer, discard_state, EndOfContainer)
from .util import last
from .style import Styled, PARENT_STYLE

__all__ = ['Flowable', 'FlowableStyle',
           'DummyFlowable', 'WarnFlowable', 'SetMetadataFlowable',
           'AddToFrontMatter',
           'InseparableFlowables', 'GroupedFlowables', 'StaticGroupedFlowables',
           'LabeledFlowable', 'GroupedLabeledFlowables',
           'HorizontallyAlignedFlowable', 'HorizontallyAlignedFlowableStyle',
           'HorizontallyAlignedFlowableState',
           'Float',
           'PageBreak', 'PageBreakStyle']


class FlowableStyle(ShapeStyle):
    """The :class:`Style` for :class:`Flowable` objects. It has the following
    attributes:

    * `space_above`: Vertical space preceding the flowable (:class:`Dimension`)
    * `space_below`: Vertical space following the flowable (:class:`Dimension`)
    * `margin_left`: Left margin (class:`Dimension`).
    * `margin_right`: Right margin (class:`Dimension`).
    * `horizontal_align`: Alignment of the rendered flowable between the left
                          and right margins (`LEFT`, `CENTER` or `RIGHT`).
    """

    attributes = {'space_above': 0,
                  'space_below': 0,
                  'margin_left': 0,
                  'margin_right': 0,
                  'padding_left': 0,
                  'padding_right': 0,
                  'padding_top': 0,
                  'padding_bottom': 0,

                  # override LineStyle/ShapeStyle defaults
                  'stroke_color': None,
                  'fill_color': None}

    default_base = None


class FlowableState(object):
    """Stores a :class:`Flowable`\'s rendering state, which can be copied. This
    enables saving the rendering state at certain points in the rendering
    process, so rendering can later be resumed at those points, if needed."""

    def __init__(self, _initial=True):
        self.initial = _initial

    def __copy__(self):
        raise NotImplementedError


class Flowable(Styled):
    """An element that can be 'flowed' into a :class:`Container`. A flowable can
    adapt to the width of the container, or it can horizontally align itself in
    the container."""

    style_class = FlowableStyle

    def __init__(self, id=None, style=None, parent=None):
        """Initialize this flowable and associate it with the given `style` and
        `parent` (see :class:`Styled`)."""
        super().__init__(style=style, parent=parent)
        self.id = id

    def get_id(self, document):
        return self.id

    @property
    def level(self):
        try:
            return self.parent.level
        except AttributeError:
            return 0

    @property
    def section(self):
        try:
            return self.parent.section
        except AttributeError:
            return None

    def flow(self, container, last_descender, state=None, **kwargs):
        """Flow this flowable into `container` and return the vertical space
        consumed.

        The flowable's contents is preceded by a vertical space with a height
        as specified in its style's `space_above` attribute. Similarly, the
        flowed content is followed by a vertical space with a height given
        by the `space_below` style attribute."""
        document = container.document
        if not state:
            container.advance(float(self.get_style('space_above', container)))
        margin_left = self.get_style('margin_left', container)
        margin_right = self.get_style('margin_right', container)
        right = container.width - margin_right
        with InlineDownExpandingContainer('MARGIN', container, left=margin_left,
                                          right=right) as margin_container:
            margin_container._flowable = self
            initial_before = True if state is None else state.initial
            initial_after = True
            try:
                width, descender = self.flow_inner(margin_container,
                                                   last_descender, state=state,
                                                   **kwargs)
                initial_after = False
            except EndOfContainer as eoc:
                if eoc.flowable_state:
                    initial_after = eoc.flowable_state.initial
                raise eoc
            finally:
                reference_id = self.get_id(container.document)
                if reference_id and initial_before and not initial_after:
                    destination = NamedDestination(str(reference_id))
                    margin_container.canvas.annotate(destination, 0, 0,
                                                     margin_container.width,
                                                     None)
        container.advance(float(self.get_style('space_below', container)), True)
        return margin_left + width + margin_right, descender

    def flow_inner(self, container, descender, state=None, **kwargs):
        draw_top = state is None or state.initial
        padding_top = self.get_style('padding_top', container)
        padding_left = self.get_style('padding_left', container)
        padding_right = self.get_style('padding_right', container)
        padding_bottom = float(self.get_style('padding_bottom', container))
        pad_kwargs = dict(left=padding_left,
                          right=container.width - padding_right,
                          extra_space_below=padding_bottom)
        try:
            container.advance(padding_top)
            with InlineDownExpandingContainer('PADDING', container,
                                              **pad_kwargs) as pad_cntnr:
                width, descender = self.render(pad_cntnr, descender,
                                               state=state, **kwargs)
            self.render_frame(container, container.height, top=draw_top)
            return width, descender
        except EndOfContainer as eoc:
            if eoc.flowable_state and not eoc.flowable_state.initial:
                self.render_frame(container, container.max_height,
                                  top=draw_top, bottom=False)
            raise

    def render_frame(self, container, container_height, top=True, bottom=True):
        width, height = float(container.width), - float(container_height)
        stroke_width = self.get_style('stroke_width', container)
        stroke_color = self.get_style('stroke_color', container)
        fill_color = self.get_style('fill_color', container)
        fill_style = ShapeStyle(stroke_color=None, fill_color=fill_color)
        rect = Rectangle((0, 0), width, height, style=fill_style, parent=self)
        rect.render(container)
        style = dict(style=LineStyle(stroke_width=stroke_width,
                                     stroke_color=stroke_color))
        if top:
            Line((0, 0), (width, 0), **style).render(container)
        Line((0, 0), (0, height), **style).render(container)          # left
        Line((width, 0), (width, height), **style).render(container)  # right
        if bottom:
            Line((0, height), (width, height), **style).render(container)

    def render(self, container, descender, state=None):
        """Renders the flowable's content to `container`, with the flowable's
        top edge lining up with the container's cursor. `descender` is the
        descender height of the preceding line or `None`."""
        raise NotImplementedError


# flowables that do not render anything (but with optional side-effects)

class DummyFlowable(Flowable):
    style_class = None

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def flow(self, container, last_descender, state=None):
        return 0, last_descender


class WarnFlowable(DummyFlowable):
    def __init__(self, message, parent=None):
        super().__init__(parent=parent)
        self.message = message

    def flow(self, container, last_descender, state=None):
        self.warn(self.message, container)
        return super().flow(container, last_descender, state)


class SetMetadataFlowable(DummyFlowable):
    def __init__(self, parent=None, **metadata):
        super().__init__(parent=parent)
        self.metadata = metadata

    def build_document(self, document):
        document.metadata.update(self.metadata)


class AddToFrontMatter(DummyFlowable):
    def __init__(self, flowables, parent=None):
        super().__init__(parent=parent)
        self.flowables = flowables

    def build_document(self, document):
        document.front_matter.append(self.flowables)


# grouping flowables

class InseparableFlowables(Flowable):
    def render(self, container, last_descender, state=None):
        max_flowable_width = 0
        with MaybeContainer(container) as maybe_container, discard_state():
            for flowable in self.flowables(container.document):
                width, last_descender = flowable.flow(maybe_container,
                                                      last_descender)
                max_flowable_width = max(max_flowable_width, width)
        return max_flowable_width, last_descender


class GroupedFlowablesState(FlowableState):
    def __init__(self, flowables, first_flowable_state=None, _initial=True):
        super().__init__(_initial)
        self.flowables = flowables
        self.first_flowable_state = first_flowable_state

    def __copy__(self):
        copy_list_items, self.flowables = tee(self.flowables)
        copy_first_flowable_state = copy(self.first_flowable_state)
        return self.__class__(copy_list_items, copy_first_flowable_state,
                              _initial=self.initial)

    def next_flowable(self):
        return next(self.flowables)

    def prepend(self, flowable, first_flowable_state):
        self.flowables = chain((flowable, ), self.flowables)
        if first_flowable_state:
            self.first_flowable_state = first_flowable_state
            self.initial = self.initial and first_flowable_state.initial


class GroupedFlowablesStyle(FlowableStyle):
    attributes = {'flowable_spacing': 0}


class GroupedFlowables(Flowable):
    style_class = GroupedFlowablesStyle

    def flowables(self, container):
        raise NotImplementedError

    def render(self, container, descender, state=None, **kwargs):
        max_flowable_width = 0
        flowables = self.flowables(container)
        item_spacing = self.get_style('flowable_spacing', container)
        state = state or GroupedFlowablesState(flowables)
        try:
            flowable = state.next_flowable()
            while True:
                flowable.parent = self
                width, descender = \
                    flowable.flow(container, descender,
                                  state=state.first_flowable_state, **kwargs)
                max_flowable_width = max(max_flowable_width, width)
                state.initial = False
                state.first_flowable_state = None
                flowable = state.next_flowable()
                container.advance(item_spacing, True)
        except EndOfContainer as eoc:
            state.prepend(flowable, eoc.flowable_state)
            raise EndOfContainer(state, eoc.page_break)
        except StopIteration:
            return max_flowable_width, descender


class StaticGroupedFlowables(GroupedFlowables):
    def __init__(self, flowables, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.children = []
        for flowable in flowables:
            self.append(flowable)

    def append(self, flowable):
        flowable.parent = self
        self.children.append(flowable)

    def flowables(self, container):
        return iter(self.children)

    def build_document(self, document):
        super().build_document(document)
        for flowable in self.flowables(document):
            flowable.build_document(document)

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        for flowable in self.flowables(flowable_target.document):
            flowable.parent = self
            flowable.prepare(flowable_target)


class LabeledFlowableStyle(FlowableStyle):
    attributes = {'label_min_width': 12*PT,
                  'label_max_width': 80*PT,
                  'label_spacing': 3*PT,
                  'wrap_label': False}


class LabeledFlowable(Flowable):
    style_class = LabeledFlowableStyle

    def __init__(self, label, flowable, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.label = label
        self.flowable = flowable
        label.parent = flowable.parent = self

    def prepare(self, flowable_target):
        self.label.prepare(flowable_target)
        self.flowable.prepare(flowable_target)

    def label_width(self, container):
        virtual_container = VirtualContainer(container)
        label_width, _ = self.label.flow(virtual_container, 0)
        return label_width

    def render(self, container, last_descender, state=None,
               max_label_width=None):
        # TODO: line up baseline of label and first flowable
        label_column_min_width = self.get_style('label_min_width', container)
        label_column_max_width = self.get_style('label_max_width', container)
        label_spacing = self.get_style('label_spacing', container)
        wrap_label = self.get_style('wrap_label', container)

        label_width = self.label_width(container)
        max_label_width = max_label_width or label_width
        label_column_width = max(label_column_min_width,
                                 min(max_label_width, label_column_max_width))
        left = label_column_width + label_spacing
        label_spillover = not wrap_label and label_width > label_column_width

        def render_label(container):
            width = None if label_spillover else label_column_width
            with InlineDownExpandingContainer('LABEL', container, width=width,
                    advance_parent=False) as label_container:
                _, descender = self.label.flow(label_container, last_descender)
            return label_container.cursor, descender

        def render_content(container, descender):
            with InlineDownExpandingContainer('CONTENT', container, left=left,
                    advance_parent=False) as content_container:
                width, descender = self.flowable.flow(content_container,
                                                      descender, state=state)
            return width, content_container.cursor, descender

        max_width = 0
        with MaybeContainer(container) as maybe_container:
            if not state or state.initial:
                with discard_state():
                    label_height, label_desc = render_label(maybe_container)
                    if label_spillover:
                        maybe_container.advance(label_height)
                        last_descender = label_desc
            else:
                label_height = label_desc = 0
            width, content_height, content_desc = \
                render_content(maybe_container, last_descender)
            max_width = max(max_width, width)
            if label_spillover:
                container.advance(content_height)
                descender = content_desc
            else:
                if content_height > label_height:
                    container.advance(content_height)
                    descender = content_desc
                else:
                    container.advance(label_height)
                    descender = label_desc
        return left + max_width, descender


class GroupedLabeledFlowables(GroupedFlowables):
    def _calculate_label_width(self, container):
        return max(flowable.label_width(container)
                   for flowable in self.flowables(container))

    def render(self, container, descender, state=None):
        if state is None:
            max_label_width = self._calculate_label_width(container)
        else:
            max_label_width = state.max_label_width
        try:
            return super().render(container, descender, state=state,
                                  max_label_width=max_label_width)
        except EndOfContainer as eoc:
            eoc.flowable_state.max_label_width = max_label_width
            raise


LEFT = 'left'
CENTER = 'center'
RIGHT = 'right'


class HorizontallyAlignedFlowableStyle(FlowableStyle):
    attributes = {'horizontal_align': LEFT}


class HorizontallyAlignedFlowableState(FlowableState):
    @property
    def width(self):
        raise NotImplementedError


class HorizontallyAlignedFlowable(Flowable):
    style_class = HorizontallyAlignedFlowableStyle

    def _align(self, container, width):
        align = self.get_style('horizontal_align', container)
        if align == LEFT or width is None:
            return
        left_extra = float(container.width - width)
        if align == CENTER:
            left_extra /= 2
        container.left = float(container.left) + left_extra

    def flow(self, container, last_descender, state=None):
        with MaybeContainer(container) as align_container:
            try:
                width, descender = super().flow(align_container, last_descender,
                                                state)
            except EndOfContainer as eoc:
                width = eoc.flowable_state.width if eoc.flowable_state else None
                raise
            finally:
                self._align(align_container, width)
        return container.width, descender


class Float(Flowable):
    """Transform a :class:`Flowable` into a floating element. A floating element
    or 'float' is not flowed into its designated container, but is forwarded to
    another container pointed to by the former's :attr:`Container.float_space`
    attribute.

    This is typically used to place figures and tables at the top or bottom of a
    page, instead of in between paragraphs."""

    def __init__(self, flowable, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.flowable = flowable
        flowable.parent = self

    def prepare(self, flowable_target):
        self.flowable.prepare(flowable_target)

    def flow(self, container, last_descender, state=None):
        """Flow contents into the float space associated with `container`."""
        if self not in container.document.floats:
            self.flowable.flow(container.float_space, None)
            container.document.floats.add(self)
            container.page.check_overflow()
        return 0, last_descender


class PageBreakStyle(FlowableStyle):
    attributes = {'page_break': False}    # False, True (any), LEFT, RIGHT


class PageBreak(Flowable):
    style_class = PageBreakStyle

    def flow(self, container, last_descender, state=None):
        page_break = self.get_style('page_break', container)
        if page_break and not state:
            top_container = container.chained_ancestor
            rev_page_conts_on_page = \
                takewhile(lambda c: c.page is not container.page,
                          reversed(top_container.chain.containers))
            first_container_on_page = last(rev_page_conts_on_page)

            next_page_type = LEFT if container.page.number % 2 else RIGHT
            if (next_page_type == page_break
                or (top_container is not first_container_on_page
                    and top_container.cursor > 0)):
                raise EndOfContainer(page_break=True)
        return super().flow(container, last_descender, state)

    def render(self, container, descender, state=None):
        return 0, descender