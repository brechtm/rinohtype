# This file is part of rinohtype, the Python document preparation system.
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


from contextlib import contextmanager
from copy import copy
from itertools import chain, tee

from .attribute import Attribute, OptionSet, Bool
from .color import Color
from .dimension import Dimension, PT
from .draw import ShapeStyle, Rectangle, Line, LineStyle, Stroke
from .layout import (InlineDownExpandingContainer, VirtualContainer,
                     MaybeContainer, discard_state, ContainerOverflow,
                     EndOfContainer, PageBreakException)
from .style import Styled, Style
from .text import StyledText
from .util import ReadAliasAttribute, NotImplementedAttribute


__all__ = ['Flowable', 'FlowableStyle',
           'DummyFlowable', 'AnchorFlowable', 'WarnFlowable',
           'SetMetadataFlowable', 'AddToFrontMatter',
           'InseparableFlowables', 'GroupedFlowables', 'StaticGroupedFlowables',
           'LabeledFlowable', 'GroupedLabeledFlowables',
           'HorizontallyAlignedFlowable', 'HorizontallyAlignedFlowableStyle',
           'Float',
           'PageBreak', 'PageBreakStyle']


class FlowableStyle(Style):
    space_above = Attribute(Dimension, 0, 'Vertical space preceding the '
                                              'flowable')
    space_below = Attribute(Dimension, 0, 'Vertical space following the '
                                              'flowable')
    margin_left = Attribute(Dimension, 0, 'Left margin')
    margin_right = Attribute(Dimension, 0, 'Right margin')
    padding_left = Attribute(Dimension, 0, 'Left padding')
    padding_right = Attribute(Dimension, 0, 'Right padding')
    padding_top = Attribute(Dimension, 0, 'Top padding')
    padding_bottom = Attribute(Dimension, 0, 'Bottom padding')
    keep_with_next = Attribute(Bool, False, 'Keep this flowable and the next '
                                            'on the same page')
    border = Attribute(Stroke, None, 'Border surrounding the flowable')
    border_left = Attribute(Stroke, None, 'Border left of the flowable')
    border_right = Attribute(Stroke, None, 'Border right of the flowable')
    border_top = Attribute(Stroke, None, 'Border above the flowable')
    border_bottom = Attribute(Stroke, None, 'Border below the flowable')
    background_color = Attribute(Color, None, "Color of the area within the "
                                              "flowable's borders")
    hide = Attribute(Bool, False, 'Suppress rendering the flowable')

    default_base = None


class FlowableState(object):
    """Stores a flowable's rendering state, which can be copied.

    This enables saving the rendering state at certain points in the rendering
    process, so rendering can later be resumed at those points, if needed.

    """

    def __init__(self, flowable, _initial=True):
        self.flowable = flowable
        self.initial = _initial

    def __copy__(self):
        return self.__class__(self.flowable, _initial=self.initial)


class Flowable(Styled):
    """A document element that can be "flowed" into a container on the page.

    A flowable can adapt to the width of the container, or it can horizontally
    align itself in the container (see :class:`HorizontallyAlignedFlowable`).

    """

    style_class = FlowableStyle

    def __init__(self, id=None, style=None, parent=None):
        """Initialize this flowable and associate it with the given `style` and
        `parent` (see :class:`Styled`)."""
        super().__init__(id=id, style=style, parent=parent)
        self.annotation = None

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

    def initial_state(self, container):
        return FlowableState(self)

    def mark_page_nonempty(self, container):
        if not self.get_style('keep_with_next', container):
            container.mark_page_nonempty()

    def flow(self, container, last_descender, state=None, **kwargs):
        """Flow this flowable into `container` and return the vertical space
        consumed.

        The flowable's contents is preceded by a vertical space with a height
        as specified in its style's `space_above` attribute. Similarly, the
        flowed content is followed by a vertical space with a height given
        by the `space_below` style attribute."""
        if self.get_style('hide', container):
            return 0, 0, last_descender

        top_to_baseline = 0
        state = state or self.initial_state(container)
        if state.initial:
            space_above = self.get_style('space_above', container)
            try:
                container.advance(float(space_above))
            except ContainerOverflow:
                raise EndOfContainer(state)
            top_to_baseline += float(space_above)
        margin_left = self.get_style('margin_left', container)
        margin_right = self.get_style('margin_right', container)
        reference_id = self.get_id(container.document, create=False)
        right = container.width - margin_right
        container.register_styled(self, continued=not state.initial)
        with InlineDownExpandingContainer('MARGIN', container, left=margin_left,
                                          right=right) as margin_container:
            initial_before, initial_after = state.initial, True
            try:
                width, inner_top_to_baseline, descender = \
                    self.flow_inner(margin_container, last_descender,
                                    state=state, **kwargs)
                top_to_baseline += inner_top_to_baseline
                initial_after = False
            except EndOfContainer as eoc:
                initial_after = eoc.flowable_state.initial
                raise eoc
            finally:
                if self.annotation:
                    height = float(margin_container.height)
                    margin_container.canvas.annotate(self.annotation,
                                                     0, 0, width, height)
                self.mark_page_nonempty(container)
                if initial_before and not initial_after:
                    if reference_id:
                        self.create_destination(margin_container, True)
        container.advance(float(self.get_style('space_below', container)), True)
        container.document.progress(self, container)
        return margin_left + width + margin_right, top_to_baseline, descender

    def flow_inner(self, container, descender, state=None, **kwargs):
        draw_top = state.initial
        padding_top = self.get_style('padding_top', container)
        padding_left = self.get_style('padding_left', container)
        padding_right = self.get_style('padding_right', container)
        padding_bottom = float(self.get_style('padding_bottom', container))
        pad_kwargs = dict(left=padding_left,
                          right=container.width - padding_right,
                          extra_space_below=padding_bottom)
        try:
            container.advance(padding_top)
        except ContainerOverflow:
            raise EndOfContainer(state)
        try:
            with InlineDownExpandingContainer('PADDING', container,
                                              **pad_kwargs) as pad_cntnr:
                width, first_line_ascender, descender = \
                    self.render(pad_cntnr, descender, state=state, **kwargs)
            self.render_frame(container, container.height, top=draw_top)
            top_to_baseline = padding_top + first_line_ascender
            return width, top_to_baseline, descender
        except EndOfContainer as eoc:
            if not eoc.flowable_state.initial:
                self.render_frame(container, container.max_height,
                                  top=draw_top, bottom=False)
            raise

    def render_frame(self, container, container_height, top=True, bottom=True):
        width, height = float(container.width), - float(container_height)
        border = self.get_style('border', container)
        border_left = self.get_style('border_left', container) or border
        border_right = self.get_style('border_right', container) or border
        border_top = self.get_style('border_top', container) or border
        border_bottom = self.get_style('border_bottom', container) or border
        background_color = self.get_style('background_color', container)
        fill_style = ShapeStyle(stroke=None, fill_color=background_color)
        rect = Rectangle((0, 0), width, height, style=fill_style, parent=self)
        rect.render(container)

        def render_border(start, end, stroke):
            Line(start, end, style=LineStyle(stroke=stroke)).render(container)

        if top:
            render_border((0, 0), (width, 0), border_top)
        render_border((0, 0), (0, height), border_left)
        render_border((width, 0), (width, height), border_right)
        if bottom:
            render_border((0, height), (width, height), border_bottom)

    def render(self, container, descender, state, **kwargs):
        """Renders the flowable's content to `container`, with the flowable's
        top edge lining up with the container's cursor. `descender` is the
        descender height of the preceding line or `None`."""
        raise NotImplementedError


# flowables that do not render anything (but with optional side-effects)

class DummyFlowable(Flowable):
    """A flowable that does not directly place anything on the page.

    Subclasses can produce side-effects to affect the output in another way.

    """

    style_class = None

    def __init__(self, id=None, parent=None):
        super().__init__(id=id, parent=parent)

    def get_style(self, attribute, flowable_target):
        if attribute == 'keep_with_next':
            return True
        raise TypeError

    def flow(self, container, last_descender, state=None, **kwargs):
        return 0, 0, last_descender


class AnchorFlowable(DummyFlowable):
    """A dummy flowable that registers a destination anchor.

    Places a destination for the flowable's ID at the current cursor position.

    """

    def flow(self, container, last_descender, state=None, **kwargs):
        self.create_destination(container, True)
        return super().flow(container, last_descender, state=state, **kwargs)


class WarnFlowable(DummyFlowable):
    """A dummy flowable that emits a warning during the rendering stage.

    Args:
        message (str): the warning message to emit

    """

    def __init__(self, message, parent=None):
        super().__init__(parent=parent)
        self.message = message

    def flow(self, container, last_descender, state=None, **kwargs):
        self.warn(self.message, container)
        return super().flow(container, last_descender, state)


class SetMetadataFlowable(DummyFlowable):
    """A dummy flowable that stores metadata in the document.

    The metadata is passed as keyword arguments. It will be available to other
    flowables during the rendering stage.

    """

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

# TODO: duplicates keep_with_next behavior - remove?
class InseparableFlowables(Flowable):
    def render(self, container, last_descender, state, **kwargs):
        max_flowable_width = 0
        first_top_to_baseline = None
        with MaybeContainer(container) as maybe_container, \
                discard_state(state):
            for flowable in self.flowables(container.document):
                width, top_to_baseline, last_descender = \
                    flowable.flow(maybe_container, last_descender)
                max_flowable_width = max(max_flowable_width, width)
                if first_top_to_baseline is None:
                    first_top_to_baseline = top_to_baseline
        return max_flowable_width, first_top_to_baseline or 0, last_descender


class GroupedFlowablesState(FlowableState):
    def __init__(self, groupedflowables, flowables, first_flowable_state=None,
                 _initial=True):
        super().__init__(groupedflowables, _initial)
        self.flowables = flowables
        self.first_flowable_state = first_flowable_state

    groupedflowables = ReadAliasAttribute('flowable')

    def __copy__(self):
        copy_flowables, self.flowables = tee(self.flowables)
        copy_first_flowable_state = copy(self.first_flowable_state)
        return self.__class__(self.groupedflowables, copy_flowables,
                              copy_first_flowable_state, _initial=self.initial)

    def next_flowable(self):
        return next(self.flowables)

    def prepend(self, first_flowable_state):
        first_flowable = first_flowable_state.flowable
        self.flowables = chain((first_flowable, ), self.flowables)
        if first_flowable_state:
            self.first_flowable_state = first_flowable_state
            self.initial = self.initial and first_flowable_state.initial


class GroupedFlowablesStyle(FlowableStyle):
    title = Attribute(StyledText, None, 'Title to precede the flowables')
    flowable_spacing = Attribute(Dimension, 0, 'Spacing between flowables')


class GroupedFlowables(Flowable):
    """Groups a list of flowables and renders them one below the other.

    Makes sure that a flowable for which `keep_with_next` is enabled is not
    seperated from the flowable that follows it.

    Subclasses should implement :meth:`flowables`.

    """

    style_class = GroupedFlowablesStyle

    def flowables(self, container):
        """Generator yielding the :class:`Flowable`\ s to group"""
        raise NotImplementedError

    def initial_state(self, container):
        flowables_iter = self.flowables(container)
        title_text = self.get_style('title', container)
        if title_text:
            title = Paragraph(title_text, style='title')
            flowables_iter = chain((title, ), flowables_iter)
        return GroupedFlowablesState(self, flowables_iter)

    def mark_page_nonempty(self, container):
        pass   # only the children place content on the page

    def render(self, container, descender, state, first_line_only=False,
               **kwargs):
        max_flowable_width = 0
        first_top_to_baseline = None
        item_spacing = self.get_style('flowable_spacing', container)
        saved_state = copy(state)
        try:
            while True:
                width, top_to_baseline, descender = \
                    self._flow_with_next(state, container, descender,
                                         first_line_only=first_line_only,
                                         **kwargs)
                if first_top_to_baseline is None:
                    first_top_to_baseline = top_to_baseline
                max_flowable_width = max(max_flowable_width, width)
                if first_line_only:
                    break
                saved_state = copy(state)
                container.advance(item_spacing, True)
        except LastFlowableException as exc:
            descender = exc.last_descender
        except KeepWithNextException:
            raise EndOfContainer(saved_state)
        except (EndOfContainer, PageBreakException) as exc:
            state.prepend(exc.flowable_state)
            exc.flowable_state = state
            raise exc
        return max_flowable_width, first_top_to_baseline or 0, descender

    def _flow_with_next(self, state, container, descender, **kwargs):
        try:
            flowable = state.next_flowable()
        except StopIteration:
            raise LastFlowableException(descender)
        flowable.parent = self
        with MaybeContainer(container) as maybe_container:
            max_flowable_width, top_to_baseline, descender = \
                flowable.flow(maybe_container, descender,
                              state=state.first_flowable_state, **kwargs)
        state.initial = False
        state.first_flowable_state = None
        if flowable.get_style('keep_with_next', container):
            item_spacing = self.get_style('flowable_spacing', container)
            maybe_container.advance(item_spacing)
            try:
                width, _, descender = self._flow_with_next(state, container,
                                                           descender, **kwargs)
            except EndOfContainer as eoc:
                if eoc.flowable_state.initial:
                    maybe_container.do_place(False)
                    raise KeepWithNextException
                else:
                    raise eoc
            max_flowable_width = max(max_flowable_width, width)
        return max_flowable_width, top_to_baseline, descender


class KeepWithNextException(Exception):
    pass


class LastFlowableException(Exception):
    def __init__(self, last_descender):
        self.last_descender = last_descender


class StaticGroupedFlowables(GroupedFlowables):
    """Groups a static list of flowables.

    Args:
        flowables (iterable[Flowable]): the flowables to group

    """

    def __init__(self, flowables, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.children = []
        for flowable in flowables:
            self.append(flowable)

    @property
    def elements(self):
        for child in self.children:
            for element in child.elements:
                yield element

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
    label_min_width = Attribute(Dimension, 12*PT, 'Minimum label width')
    label_max_width = Attribute(Dimension, 80*PT, 'Maximum label width')
    label_spacing = Attribute(Dimension, 3*PT, 'Spacing between a label and '
                                               'the labeled flowable')
    align_baselines = Attribute(Bool, True, 'Line up the baselines of the '
                                            'label and the labeled flowable')
    wrap_label = Attribute(Bool, False, 'Wrap the label at `label_max_width`')


class LabeledFlowableState(FlowableState):
    def __init__(self, flowable, content_flowable_state, _initial=True):
        super().__init__(flowable, _initial=_initial)
        self.content_flowable_state = content_flowable_state

    def update(self, content_flowable_state=None):
        if content_flowable_state:
            self.content_flowable_state = content_flowable_state
        self.initial = self.initial and self.content_flowable_state.initial

    def __copy__(self):
        return self.__class__(self.flowable, copy(self.content_flowable_state),
                              _initial=self.initial)


class LabeledFlowable(Flowable):
    """A flowable with a label.

    The flowable and the label are rendered side-by-side. If the label exceeds
    the `label_max_width` style attribute value, the flowable is rendered below
    the label.

    Args:
        label (Flowable): the label for the flowable
        flowable (Flowable): the flowable to label

    """

    style_class = LabeledFlowableStyle

    def __init__(self, label, flowable, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.label = label
        self.flowable = flowable
        label.parent = flowable.parent = self

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        self.label.prepare(flowable_target)
        self.flowable.prepare(flowable_target)

    def label_width(self, container):
        label_max_width = self.get_style('label_max_width', container)
        virtual_container = VirtualContainer(container)
        label_width, _, _ = self.label.flow(virtual_container, 0)
        spillover = (label_width > label_max_width.to_points(container.width)
                     if label_max_width else True)
        return label_width, spillover

    def initial_state(self, container):
        initial_content_state = self.flowable.initial_state(container)
        return LabeledFlowableState(self, initial_content_state)

    def render(self, container, last_descender, state, label_column_width=None,
               **kwargs):
        def style(name):
            return self.get_style(name, container)

        label_min_width = style('label_min_width').to_points(container.width)
        label_max_width = style('label_max_width')
        if label_max_width:
            label_max_width = label_max_width.to_points(container.width)
        label_spacing = style('label_spacing')
        wrap_label = style('wrap_label')
        align_baselines = style('align_baselines')

        free_label_width, _ = self.label_width(container)

        label_spillover = False
        if label_column_width:  # part of a GroupedLabeledFlowables
            label_width = label_column_width
        elif free_label_width < label_min_width:
            label_width = label_min_width
        elif label_max_width and free_label_width <= label_max_width:
            label_width = free_label_width
        else:
            label_width = label_min_width

        if not label_max_width:
            label_spillover = True
        elif free_label_width > label_width:
            if wrap_label:
                vcontainer = VirtualContainer(container, width=label_max_width)
                wrapped_width, _, _ = self.label.flow(vcontainer, 0)
                if wrapped_width < label_max_width:
                    label_width = wrapped_width
                else:
                    label_width = label_min_width
                    label_spillover = True
            else:
                label_spillover = True

        left = label_width + label_spacing
        label_cntnr_width = None if label_spillover else label_width

        if align_baselines and (state.initial and not label_spillover):
            label_baseline = find_baseline(self.label, container,
                                           last_descender,
                                           width=label_cntnr_width)
            content_state_copy = copy(state.content_flowable_state)
            content_baseline = find_baseline(self.flowable, container,
                                             last_descender, left=left,
                                             state=content_state_copy)
        else:
            label_baseline = content_baseline = 0
        top_to_baseline = max(label_baseline, content_baseline)
        offset_label = top_to_baseline - label_baseline
        offset_content = top_to_baseline - content_baseline
        rendering_content = False
        try:
            with MaybeContainer(container) as maybe_container:
                if state.initial:
                    with inline_container('LABEL', maybe_container,
                                  width=label_cntnr_width) as label_container:
                        label_container.advance(offset_label)
                        _, _, label_descender = self.label.flow(label_container,
                                                                last_descender)
                        label_height = label_container.height
                    if label_spillover:
                        maybe_container.advance(label_height)
                        last_descender = label_descender
                else:
                    label_height = label_descender = 0
                maybe_container.advance(offset_content)
                rendering_content = True
                with inline_container('CONTENT', maybe_container,
                                      left=left) as content_container:
                    width, _, content_descender \
                        = self.flowable.flow(content_container, last_descender,
                                             state=state.content_flowable_state)
                content_height = content_container.cursor
        except (ContainerOverflow, EndOfContainer) as eoc:
            content_state = eoc.flowable_state if rendering_content else None
            state.update(content_state)
            raise EndOfContainer(state)
        if label_spillover or content_height > label_height:
            container.advance(content_height)
            descender = content_descender
        else:
            container.advance(label_height)
            descender = label_descender
        return left + width, label_baseline, descender


def find_baseline(flowable, container, last_descender, state=None, **kwargs):
    virtual_container = VirtualContainer(container)
    with inline_container('DUMMY', virtual_container, **kwargs) as inline_ctnr:
        _, baseline, _ = flowable.flow(inline_ctnr, last_descender,
                                       state=state, first_line_only=True)
    return baseline


@contextmanager
def inline_container(name, container, **kwargs):
    with InlineDownExpandingContainer(name, container, advance_parent=False,
                                      **kwargs) as container:
        yield container


class GroupedLabeledFlowables(GroupedFlowables):
    """Groups a list of labeled flowables, lining them up.



    """

    def _calculate_label_width(self, container):
        max_width = 0
        for flowable in self.flowables(container):
            width, splillover = flowable.label_width(container)
            if not splillover:
                max_width = max(max_width, width)
        return max_width

    def render(self, container, descender, state, **kwargs):
        if state.initial:
            max_label_width = self._calculate_label_width(container)
        else:
            max_label_width = state.max_label_width
        try:
            return super().render(container, descender, state=state,
                                  label_column_width=max_label_width)
        except EndOfContainer as eoc:
            eoc.flowable_state.max_label_width = max_label_width
            raise


class HorizontalAlignment(OptionSet):
    values = 'left', 'right', 'center'


class HorizontallyAlignedFlowableStyle(FlowableStyle):
    width = Attribute(Dimension, None, 'The width of the flowable')
    horizontal_align = Attribute(HorizontalAlignment, 'left',
                                 'Horizontal alignment of the flowable')


class HorizontallyAlignedFlowableState(FlowableState):
    width = NotImplementedAttribute()


class HorizontallyAlignedFlowable(Flowable):
    """A flowable with configurable width and horizontal alignment.

    The `width` and `horizontal_align` control the width and horizontal
    alignment of the flowable.

    """

    style_class = HorizontallyAlignedFlowableStyle

    def __init__(self, *args, align=None, width=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.align = align
        self.width = width

    def _align(self, container, width):
        align = self.align or self.get_style('horizontal_align', container)
        if align == HorizontalAlignment.LEFT or width is None:
            return
        left_extra = float(container.width - width)
        if align == HorizontalAlignment.CENTER:
            left_extra /= 2
        container.left = float(container.left) + left_extra

    def _width(self, container):
        return self.width or self.get_style('width', container)

    def flow(self, container, last_descender, state=None, **kwargs):
        width = None
        with MaybeContainer(container) as align_container:
            try:
                width, top_to_baseline, descender = \
                    super().flow(align_container, last_descender, state)
            except EndOfContainer as eoc:
                try:
                    width = eoc.flowable_state.width
                except AttributeError:  # image was not found, a Paragraph with
                    pass                # a warning message was placed instead
                raise eoc
            finally:
                self._align(align_container, width)
        return container.width, top_to_baseline, descender


class FloatStyle(FlowableStyle):
    float = Attribute(Bool, False, 'Float the flowable to the top or bottom '
                                   'of the page')


class Float(Flowable):
    """A flowable that can optionally be placed elsewhere on the page.

    If this flowable's `float` style attribute is set to ``True``, it is not
    flowed in line with the surrounding flowables, but it is instead flowed
    into another container pointed to by the former's
    :attr:`Container.float_space` attribute.

    This is typically used to place figures and tables at the top or bottom of
    a page, instead of in between paragraphs.

    """

    def flow(self, container, last_descender, state=None, **kwargs):
        if self.get_style('float', container):
            id = self.get_id(container.document)
            if id not in container.document.floats:
                super().flow(container.float_space, None)
                container.document.floats.add(id)
                container.page.check_overflow()
            return 0, 0, last_descender
        else:
            return super().flow(container, last_descender, state=state,
                                **kwargs)


class Break(OptionSet):
    values = None, 'any', 'left', 'right'


class PageBreakStyle(FlowableStyle):
    page_break = Attribute(Break, None, 'Type of page break to insert '
                                        'before rendering this flowable')


class PageBreak(Flowable):
    """A flowable that optionally triggers a page break before rendering.

    If this flowable's `page_break` style attribute is not ``None``, it breaks
    to the page of the type indicated by `page_break` before starting
    rendering.

    """

    style_class = PageBreakStyle
    exception_class = PageBreakException

    def flow(self, container, last_descender, state=None, **kwargs):
        state = state or self.initial_state(container)
        page_number = container.page.number
        this_page_type = 'left' if page_number % 2 == 0 else 'right'
        page_break = self.get_style('page_break', container)
        if state.initial and page_break:
            if not (container.page._empty
                    and page_break in (Break.ANY, this_page_type)):
                if page_break == Break.ANY:
                    page_break = 'left' if page_number % 2 else 'right'
                chain = container.top_level_container.chain
                raise self.exception_class(page_break, chain, state)
        return super().flow(container, last_descender, state)

    def render(self, container, descender, state, **kwargs):
        return 0, 0, descender


from .paragraph import Paragraph
