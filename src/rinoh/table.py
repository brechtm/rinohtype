# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections.abc import Iterable
from itertools import chain
from functools import partial
from math import sqrt
from token import NAME

from .attribute import (Attribute, OptionSet, OverrideDefault, Integer, Bool,
                        AcceptNoneAttributeType, ParseError)
from .dimension import DimensionBase as DimBase, Dimension, PERCENT
from .draw import Line, Rectangle, ShapeStyle, LineStyle
from .flowable import (Flowable, FlowableStyle, FlowableState, FlowableWidth,
                       Float, FloatStyle)
from .layout import MaybeContainer, VirtualContainer, EndOfContainer
from .structure import (StaticGroupedFlowables, GroupedFlowablesStyle,
                        ListOf, ListOfSection)
from .style import Styled
from .util import ReadAliasAttribute, INF


__all__ = ['Table', 'TableStyle', 'TableWithCaption',
           'TableSection', 'TableHead', 'TableBody', 'TableRow',
           'TableCell', 'TableCellStyle',
           'TableCellBorder', 'TableCellBorderStyle',
           'TableCellBackground', 'TableCellBackgroundStyle', 'VerticalAlign',
           'ListOfTables', 'ListOfTablesSection']


class TableState(FlowableState):
    table = ReadAliasAttribute('flowable')

    def __init__(self, table, column_widths=None, body_row_index=0):
        super().__init__(table)
        self.column_widths = column_widths
        self.body_row_index = body_row_index

    @property
    def width(self):
        return sum(self.column_widths)

    @property
    def body_row_index(self):
        return self._body_row_index

    @body_row_index.setter
    def body_row_index(self, body_row_index):
        self._body_row_index = body_row_index
        self.initial = body_row_index == 0

    def __copy__(self):
        return self.__class__(self.table, self.column_widths,
                              self.body_row_index)


class Auto:
    @classmethod
    def from_tokens(cls, tokens, source):
        token = next(tokens)
        if token.type != NAME or token.string.lower() != 'auto':
            raise ParseError("Expecting the 'auto' keyword")
        return None


class ColumnWidths(AcceptNoneAttributeType):
    @classmethod
    def check_type(cls, value):
        return (super().check_type(value)
                or (isinstance(value, list)
                    and all(item is None or isinstance(item, (Dimension, int))
                            for item in value)))

    @classmethod
    def from_tokens(cls, tokens, source):
        items = []
        while tokens.next.type:
            for cls in (Dimension, Integer, Auto):
                tokens.push_state()
                try:
                    items.append(cls.from_tokens(tokens, source))
                    tokens.pop_state(discard=True)
                    break
                except ParseError:
                    tokens.pop_state(discard=False)
            else:
                raise ParseError("Expecting a dimension, integer or 'auto'")
        return items

    @classmethod
    def doc_format(cls):
        return ("a whitespace-delimited list of column widths;"
                " :class:`.Dimension`\\ s (absolute width), integers (relative"
                " width) and/or 'auto' (automatic width)")


class TableStyle(FlowableStyle):
    column_widths = Attribute(ColumnWidths, None, 'Absolute or relative widths'
                                                  ' of each column')
    split_minimum_rows = Attribute(Integer, 0, 'The minimum number of rows to '
                                               'display when the table is '
                                               'split across pages')
    repeat_head = Attribute(Bool, False, 'Repeat the head when the table is '
                                         'split across pages')


NEVER_SPLIT = float('+inf')


class Table(Flowable):
    style_class = TableStyle

    def __init__(self, body, head=None, align=None, width=None,
                 column_widths=None, id=None, style=None, parent=None):
        """

        Args:
          width (DimensionBase or None): the width of the table. If ``None``,
              the width of the table is automatically determined.
          column_widths (list or None): a list of relative (int or float)
              and absolute (:class:`.Dimension`) column widths. A value of
              ``None`` auto-sizes the column. Passing ``None` instead of a list
              auto-sizes all columns.

        """
        super().__init__(align=align, width=width,
                         id=id, style=style, parent=parent)
        self.head = head
        if head:
            head.parent = self
        self.body = body
        body.parent = self
        self.column_widths = column_widths

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        if self.head:
            self.head.prepare(flowable_target)
        self.body.prepare(flowable_target)

    def initial_state(self, container):
        return TableState(self)

    def render(self, container, last_descender, state, space_below=0,
               **kwargs):
        if state.column_widths is None:
            state.column_widths = self._size_columns(container)
        get_style = partial(self.get_style, container=container)
        with MaybeContainer(container) as maybe_container:
            def render_rows(section, next_row_index=0):
                rows = section[next_row_index:]
                rendered_spans = self._render_section(container, rows,
                                                      state.column_widths)
                for rendered_rows, is_last_span in rendered_spans:
                    sum_row_heights = sum(row.height for row in rendered_rows)
                    remaining_height = maybe_container.remaining_height
                    if isinstance(section, TableBody) and is_last_span:
                        remaining_height -= space_below
                    if sum_row_heights > remaining_height:
                        break
                    self._place_rows_and_render_borders(maybe_container,
                                                        rendered_rows)
                    next_row_index += len(rendered_rows)
                return next_row_index

            # head rows
            if self.head and (state.initial or get_style('repeat_head')):
                if render_rows(self.head) != len(self.head):
                    raise EndOfContainer(state)
            # body rows
            next_row_index = render_rows(self.body, state.body_row_index)
            rows_left = len(self.body) - next_row_index
            if rows_left > 0:
                split_minimum_rows = get_style('split_minimum_rows')
                if min(next_row_index, rows_left) >= split_minimum_rows:
                    state.body_row_index = next_row_index
                raise EndOfContainer(state)
        return sum(state.column_widths), 0, 0

    def _size_columns(self, container):
        """Calculate the table's column sizes constrained by:

        - given (absolute, relative and automatic) column widths
        - full table width: fixed or automatic (container width max)
        - cell contents

        """
        num_cols = self.body.num_columns
        width = self._width(container)
        if width == FlowableWidth.FILL:
            width = 100 * PERCENT
        available_width = (float(container.width)
                           if width == FlowableWidth.AUTO
                           else width.to_points(container.width))
        column_widths = (self.column_widths
                         or self.get_style('column_widths', container)
                         or [None for _ in range(num_cols)])     # auto widths
        if len(column_widths) != num_cols:
            raise ValueError("'column_widths' length doesn't match the number"
                             " of table columns")

        # indices for fixed, relative and auto width columns
        fixed_cols = [i for i, width in enumerate(column_widths)
                      if isinstance(width, DimBase)]
        rel_cols = [i for i, width in enumerate(column_widths)
                    if width and i not in fixed_cols]
        auto_cols = [i for i, width in enumerate(column_widths)
                     if width is None]

        # fixed-width columns
        final = [width.to_points(container.width) if i in fixed_cols else None
                 for i, width in enumerate(column_widths)]
        fixed_total_width = sum(width or 0 for width in final)
        if fixed_total_width > available_width:
            self.warn('Total width of fixed-width columns exceeds the'
                      ' available width')

        # minimum (wrap content) and maximum (non wrapping) column widths
        min_widths = self._widths_from_content(final, 0, container)
        max_widths = self._widths_from_content(final, INF, container)

        # calculate max column widths respecting the specified relative
        #   column widths (padding columns with whitespace)
        rel_max_widths = [max(max(column_widths[i] / column_widths[j]
                                  * max_widths[j] for j in rel_cols if j != i),
                              max_widths[i]) if i in rel_cols else width
                          for i, width in enumerate(max_widths)]

        # does the table fit within the available width without wrapping?
        if sum(rel_max_widths) < available_width:  # no content wrapping needed
            if width == FlowableWidth.AUTO:        # -> use maximum widths
                return rel_max_widths
            rel_widths = rel_max_widths
        else:                                      # content needs wrapping
            rel_widths = [sqrt(mini * maxi)        # -> use weighted widths
                          for mini, maxi in zip(min_widths, max_widths)]

        # transform auto-width columns to relative-width columns
        if auto_cols:
            # scaling factor between supplied relative column widths and the
            #   relative widths determined for auto-sized columns
            # TODO: instead of min, use max or avg?
            auto_rel_factor = min(rel_widths[i] / column_widths[i]
                                  for i in rel_cols) if rel_cols else 1
            for i in auto_cols:
                column_widths[i] = rel_widths[i] * auto_rel_factor
            rel_cols = sorted(rel_cols + auto_cols)

        # scale relative-width columns to fill the specified/available width
        if rel_cols:
            rel_sum = sum(column_widths[i] for i in rel_cols)
            total_relative_cols_width = available_width - fixed_total_width
            rel_factor = total_relative_cols_width / rel_sum
            for i in rel_cols:
                final[i] = column_widths[i] * rel_factor

        return self._optimize_auto_columns(auto_cols, final, min_widths,
                                                max_widths, container)

    def _optimize_auto_columns(self, auto_cols, final, min_widths,
                               max_widths, container):
        """Adjust auto-sized columns to prevent content overflowing cells"""
        extra = [final[i] - min_widths[i] for i in auto_cols]
        excess = [final[i] - max_widths[i] for i in auto_cols]
        neg_extra = sum(x for x in extra if x < 0)  # width to be compensated
        if neg_extra == 0:  # everything fits within in the given column widths
            return final
        # increase width of overfilled columns to the minimum width
        for i in (i for i in auto_cols if extra[i] < 0):
            final[i] = min_widths[i]
        surplus = neg_extra + sum(x for x in excess if x > 0)
        if surplus >= 0:  # using only the unused space (padding) is enough
            for i in (i for i in auto_cols if excess[i] > 0):
                final[i] = max_widths[i]
        else:             # that isn't enough; wrap non-wrapped content instead
            surplus = neg_extra + sum(x for x in extra if x > 0)
            for i in (i for i in auto_cols if extra[i] > 0):
                final[i] = min_widths[i]
        if surplus < 0:
            self.warn('Table contents are too wide to fit within the available'
                      ' width', container)
        # divide surplus space among all auto-sized columns
        per_column_surplus = surplus / len(auto_cols)
        for i in auto_cols:
            final[i] += per_column_surplus
        return final

    def _widths_from_content(self, fixed, max_cell_width, container):
        """Calculate required column widths given a maximum cell width"""
        def cell_content_width(cell):
            buffer = VirtualContainer(container, width=max_cell_width)
            width, _, _ = cell.flow(buffer, None)
            return float(width)

        widths = [width if width else 0 for width in fixed]
        fixed_width_cols = set(i for i, width in enumerate(widths) if width)

        # find the maximum content width for all non-column-spanning cells for
        #   each non-fixed-width column
        for row in chain(self.head or [], self.body):
            for cell in (cell for cell in row if cell.colspan == 1):
                col = int(cell.column_index)
                if col not in fixed_width_cols:
                    widths[col] = max(widths[col], cell_content_width(cell))

        # divide the extra space needed for column-spanning cells equally over
        #   the spanned columns (skipping fixed-width columns)
        for row in chain(self.head or [], self.body):
            for cell in (cell for cell in row if cell.colspan > 1):
                c = int(cell.column_index)
                c_end = c + cell.colspan
                extra = cell_content_width(cell) - sum(widths[c:c_end])
                non_fixed_cols = [i for i in range(c, c_end)
                                  if i not in fixed_width_cols]
                if extra > 0 and non_fixed_cols:
                    per_column_extra = extra / len(non_fixed_cols)
                    for i in non_fixed_cols:
                        widths[i] += per_column_extra
        return widths

    @classmethod
    def _render_section(cls, container, rows, column_widths):
        rendered_rows = []
        rows_left_in_span = 0
        for row in rows:
            rows_left_in_span = max(row.maximum_rowspan, rows_left_in_span) - 1
            rendered_row = cls._render_row(column_widths, container, row)
            rendered_rows.append(rendered_row)
            if rows_left_in_span == 0:
                is_last_span = row == rows[-1]
                yield cls._vertically_size_cells(rendered_rows), is_last_span
                rendered_rows = []
        assert not rendered_rows

    @staticmethod
    def _render_row(column_widths, container, row):
        rendered_row = RenderedRow(int(row._index), row)
        for cell in row:
            col_idx = int(cell.column_index)
            left = sum(column_widths[:col_idx])
            cell_width = sum(column_widths[col_idx:col_idx + cell.colspan])
            buffer = VirtualContainer(container, cell_width)
            cell.flow(buffer, None)
            rendered_cell = RenderedCell(cell, buffer, left)
            rendered_row.append(rendered_cell)
        return rendered_row

    @staticmethod
    def _vertically_size_cells(rendered_rows):
        """Grow row heights to cater for vertically spanned cells that do not
        fit in the available space."""
        for r, rendered_row in enumerate(rendered_rows):
            for rendered_cell in rendered_row:
                if rendered_cell.rowspan > 1:
                    row_height = sum(row.height for row in
                                     rendered_rows[r:r + rendered_cell.rowspan])
                    extra_height_needed = rendered_cell.height - row_height
                    if extra_height_needed > 0:
                        padding = extra_height_needed / rendered_cell.rowspan
                        for i in range(r, r + rendered_cell.rowspan):
                            rendered_rows[i].height += padding
        return rendered_rows

    @staticmethod
    def _place_rows_and_render_borders(container, rendered_rows):
        """Place the rendered cells onto the page canvas and draw borders around
        them."""
        def draw_cell_border(rendered_cell, cell_height, container):
            cell_width = rendered_cell.width
            background = TableCellBackground((0, 0), cell_width, cell_height,
                                             parent=rendered_cell.cell)
            background.render(container)
            for position in ('top', 'right', 'bottom', 'left'):
                border = TableCellBorder(rendered_cell, cell_height, position)
                border.render(container)
            return background

        y_cursor = container.cursor
        for r, rendered_row in enumerate(rendered_rows):
            container.advance(rendered_row.height)
            if rendered_row.index == 0:
                container.register_styled(rendered_row.row.parent)
            container.register_styled(rendered_row.row)
            for c, rendered_cell in enumerate(rendered_row):
                cell_height = sum(rendered_row.height for rendered_row in
                                  rendered_rows[r:r + rendered_cell.rowspan])
                x_cursor = rendered_cell.x_position
                y_pos = float(y_cursor + cell_height)
                cell_container = VirtualContainer(container)
                background = draw_cell_border(rendered_cell, cell_height,
                                              cell_container)
                cell_container.place_at(container, x_cursor, y_pos)
                vertical_align = rendered_cell.cell.get_style('vertical_align',
                                                              container)
                if vertical_align == VerticalAlign.TOP:
                    vertical_offset = 0
                elif vertical_align == VerticalAlign.MIDDLE:
                    vertical_offset = (cell_height - rendered_cell.height) / 2
                elif vertical_align == VerticalAlign.BOTTOM:
                    vertical_offset = (cell_height - rendered_cell.height)
                y_offset = float(y_cursor + vertical_offset)
                rendered_cell.container.place_at(container, x_cursor, y_offset)
                container.register_styled(background)
            y_cursor += rendered_row.height


class TableWithCaptionStyle(FloatStyle, GroupedFlowablesStyle):
    pass


class TableWithCaption(Float, StaticGroupedFlowables):
    style_class = TableWithCaptionStyle
    category = 'Table'


class TableSection(Styled, list):
    def __init__(self, rows, style=None, parent=None):
        Styled.__init__(self, style=style, parent=parent)
        list.__init__(self, rows)
        for row in rows:
            row.parent = self

    def prepare(self, flowable_target):
        for row in self:
            row.prepare(flowable_target)

    @property
    def num_columns(self):
        return sum(cell.colspan for cell in self[0])


class TableHead(TableSection):
    pass


class TableBody(TableSection):
    pass


class TableRow(Styled, list):
    def __init__(self, cells, style=None, parent=None):
        Styled.__init__(self, style=style, parent=parent)
        list.__init__(self, cells)
        for cell in cells:
            cell.parent = self

    @property
    def maximum_rowspan(self):
        return max(cell.rowspan for cell in self)

    def prepare(self, flowable_target):
        for cells in self:
            cells.prepare(flowable_target)

    @property
    def _index(self):
        return next(i for i, item in enumerate(self.parent) if item is self)

    def get_rowspanned_columns(self):
        """Return a dictionary mapping column indices to the number of columns
        spanned."""
        section = self.parent
        spanned_columns = {}
        current_row_index = self._index
        current_row_cols = sum(cell.colspan for cell in self)
        prev_rows = iter(reversed(section[:current_row_index]))
        while current_row_cols < section.num_columns:
            row = next(prev_rows)
            min_rowspan = current_row_index - int(row._index)
            if row.maximum_rowspan > min_rowspan:
                for cell in (c for c in row if c.rowspan > min_rowspan):
                    col_index = int(cell.column_index)
                    spanned_columns[col_index] = cell.colspan
                    current_row_cols += cell.colspan
        return spanned_columns


class VerticalAlign(OptionSet):
    values = 'top', 'middle', 'bottom'


class TableCellStyle(GroupedFlowablesStyle):
    vertical_align = Attribute(VerticalAlign, 'middle',
                               'Vertical alignment of the cell contents '
                               'within the available space')


class TableCell(StaticGroupedFlowables):
    style_class = TableCellStyle

    row = ReadAliasAttribute('parent')

    def __init__(self, flowables, rowspan=1, colspan=1,
                 id=None, style=None, parent=None):
        super().__init__(flowables, id=id, style=style, parent=parent)
        self.rowspan = rowspan
        self.colspan = colspan

    @property
    def row_index(self):
        return RowIndex(self)

    @property
    def column_index(self):
        return ColumnIndex(self)


class Index(object):
    def __init__(self, cell):
        self.cell = cell

    @property
    def row(self):
        return self.cell.parent

    @property
    def table_section(self):
        return self.row.parent

    def __eq__(self, other):
        if isinstance(other, slice):
            indices = range(*other.indices(self.num_items))
        elif isinstance(other, Iterable):
            indices = other
        else:
            indices = (other, )
        indices = [self.num_items + idx if idx < 0 else idx for idx in indices]
        return any(index in indices for index in self)

    def __int__(self):
        raise NotImplementedError

    def num_items(self):
        raise NotImplementedError


class RowIndex(Index):
    def __int__(self):
        return next(i for i, row in enumerate(self.table_section)
                    if row is self.row)

    def __iter__(self):
        index = int(self)
        return (index + i for i in range(self.cell.rowspan))

    @property
    def num_items(self):
        return len(self.table_section)


class ColumnIndex(Index):
    def __int__(self):
        spanned_columns = self.row.get_rowspanned_columns()
        column_index = 0
        cells = iter(self.row)
        for col_index in range(self.cell.row.parent.num_columns):
            if col_index in spanned_columns:
                column_index += spanned_columns[col_index]
            else:
                cell = next(cells)
                if cell is self.cell:
                    return column_index
                column_index += cell.colspan

    def __iter__(self):
        index = int(self)
        return (index + i for i in range(self.cell.colspan))

    @property
    def num_items(self):
        return self.row.parent.num_columns


class RenderedCell(object):
    def __init__(self, cell, container, x_position):
        self.cell = cell
        self.container = container
        self.x_position = x_position

    @property
    def width(self):
        return float(self.container.width)

    @property
    def height(self):
        return float(self.container.height)

    @property
    def rowspan(self):
        return self.cell.rowspan


class RenderedRow(list):
    def __init__(self, index, row):
        super().__init__()
        self.index = index
        self.row = row
        self.height = 0

    def append(self, rendered_cell):
        if rendered_cell.cell.rowspan == 1:
            self.height = max(self.height, rendered_cell.height)
        super().append(rendered_cell)


class TableCellBorderStyle(LineStyle):
    stroke = OverrideDefault(None)


class TableCellBorder(Line):
    style_class = TableCellBorderStyle

    def __init__(self, rendered_cell, cell_height, position, style=None):
        left, bottom, right, top = 0, 0, rendered_cell.width, cell_height
        if position == 'top':
            start, end = (left, top), (right, top)
        if position == 'right':
            start, end = (right, top), (right, bottom)
        if position == 'bottom':
            start, end = (left, bottom), (right, bottom)
        if position == 'left':
            start, end = (left, bottom), (left, top)
        super().__init__(start, end, style=style, parent=rendered_cell.cell)
        self.position = position


class TableCellBackgroundStyle(ShapeStyle):
    fill_color = OverrideDefault(None)
    stroke = OverrideDefault(None)


class TableCellBackground(Rectangle):
    style_class = TableCellBackgroundStyle


class ListOfTables(ListOf):
    category = 'Table'


class ListOfTablesSection(ListOfSection):
    list_class = ListOfTables
