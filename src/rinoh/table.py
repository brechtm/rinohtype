# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections import Iterable
from itertools import chain
from functools import partial
from math import sqrt

from .attribute import Attribute, OptionSet, OverrideDefault, Integer, Bool
from .dimension import DimensionBase as DimBase
from .draw import Line, Rectangle, ShapeStyle, LineStyle
from .flowable import (HorizontallyAlignedFlowable,
                       HorizontallyAlignedFlowableStyle,
                       HorizontallyAlignedFlowableState)
from .layout import MaybeContainer, VirtualContainer, EndOfContainer
from .structure import StaticGroupedFlowables, GroupedFlowablesStyle
from .style import Styled
from .util import ReadAliasAttribute


__all__ = ['Table', 'TableStyle', 'TableWithCaption',
           'TableSection', 'TableHead', 'TableBody', 'TableRow',
           'TableCell', 'TableCellStyle',
           'TableCellBorder', 'TableCellBorderStyle',
           'TableCellBackground', 'TableCellBackgroundStyle', 'VerticalAlign']


class TableState(HorizontallyAlignedFlowableState):
    def __init__(self, table, column_widths, body_row_index=0):
        super().__init__(table)
        self.column_widths = column_widths
        self.body_row_index = body_row_index

    table = ReadAliasAttribute('flowable')

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


class TableStyle(HorizontallyAlignedFlowableStyle):
    split_minimum_rows = Attribute(Integer, 0, 'The minimum number of rows to '
                                               'display when the table is '
                                               'split across pages')
    repeat_head = Attribute(Bool, False, 'Repeat the head when the table is '
                                         'split across pages')


NEVER_SPLIT = float('+inf')


class Table(HorizontallyAlignedFlowable):
    style_class = TableStyle

    def __init__(self, body, head=None, width=None, column_widths=None,
                 id=None, style=None, parent=None):
        """

        Args:
          width (DimensionBase or None): the width of the table. If ``None``,
              the width of the table is automatically determined.
          column_widths (list or None): a list of relative (int or float)
              and absolute (:class:`.Dimension`) column widths. A value of
              ``None`` auto-sizes the column. Passing ``None` instead of a list
              auto-sizes all columns.

        """
        super().__init__(width=width, id=id, style=style, parent=parent)
        self.head = head
        if head:
            head.parent = self
        self.body = body
        body.parent = self
        self.column_widths = column_widths

    def initial_state(self, container):
        return TableState(self, self._size_columns(container))

    def render(self, container, last_descender, state, **kwargs):
        # TODO: allow data to override style (align)
        get_style = partial(self.get_style, flowable_target=container)
        with MaybeContainer(container) as maybe_container:
            def render_rows(section, next_row_index=0):
                rows = section[next_row_index:]
                for rendered_rows in self._render_section(container, rows,
                                                          state.column_widths):
                    sum_row_heights = sum(row.height for row in rendered_rows)
                    if sum_row_heights > maybe_container.remaining_height:
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

        - requested (absolute, relative and automatic) column widths
        - container width (= available width)
        - cell contents

        """
        def calculate_column_widths(max_cell_width):
            """Calculate required column widths given a maximum cell width"""
            def cell_content_width(cell):
                buffer = VirtualContainer(container, width=max_cell_width)
                width, _, _ = cell.flow(buffer, None)
                return float(width)

            widths = [0] * self.body.num_columns
            for row in chain(self.head or [], self.body):
                for cell in (cell for cell in row if cell.colspan == 1):
                    col = int(cell.column_index)
                    widths[col] = max(widths[col], cell_content_width(cell))
            for row in chain(self.head or [], self.body):
                for cell in (cell for cell in row if cell.colspan > 1):
                    c = int(cell.column_index)
                    c_end = c + cell.colspan
                    padding = cell_content_width(cell) - sum(widths[c:c_end])
                    if padding > 0:
                        per_column_padding = padding / cell.colspan
                        for i in range(cell.colspan):
                            widths[c + i] += per_column_padding
            return widths

        width = self._width(container)
        try:
            fixed_width = width.to_points(container.width)
        except AttributeError:
            fixed_width = width or None
        min_column_widths = calculate_column_widths(0)
        max_column_widths = calculate_column_widths(float('+inf'))

        # calculate relative column widths for auto-sized columns
        auto_rel_colwidths = [sqrt(minimum * maximum) for minimum, maximum
                              in zip(min_column_widths, max_column_widths)]
        column_widths = self.column_widths or [None for _ in max_column_widths]
        try:          # TODO: max() instead of min()?
            relative_factor = min(auto_relative_width / width
                                  for width, auto_relative_width
                                  in zip(column_widths, auto_rel_colwidths)
                                  if width and not isinstance(width, DimBase))
        except ValueError:
            relative_factor = 1
        column_widths = [auto_relative_width * relative_factor
                         if width is None else width
                         for width, auto_relative_width
                         in zip(column_widths, auto_rel_colwidths)]

        # set min = max for columns with a fixed width
        total_fixed_cols_width = 0
        total_portions = 0
        for i, column_width in enumerate(column_widths):
            if isinstance(column_width, DimBase):
                width_in_pt = column_width.to_points(container.width)
                min_column_widths[i] = max_column_widths[i] = width_in_pt
                total_fixed_cols_width += width_in_pt
            else:
                total_portions += column_width

        # does the table fit within the available width without wrapping?
        if sum(max_column_widths) <= container.width:
            return max_column_widths

        # determine table width
        if fixed_width:
            table_width = fixed_width
        elif total_portions:
            max_factor = max(maximum / width for width, maximum,
                             in zip(column_widths, max_column_widths)
                             if not isinstance(width, DimBase))
            no_wrap_rel_cols_width = total_portions * max_factor
            table_width = min(total_fixed_cols_width + no_wrap_rel_cols_width,
                              float(container.width))
        else:
            table_width = total_fixed_cols_width

        # TODO: warn when a column's fixed width < min width

        # determine absolute width of columns with relative widths
        if total_portions:
            total_relative_cols_width = table_width - total_fixed_cols_width
            portion_width = total_relative_cols_width / total_portions
            auto_widths = [width if isinstance(width, DimBase)
                           else width * portion_width
                           for width in column_widths]
            extra = [0 if isinstance(width, DimBase)
                     else auto_width - min_column_widths[index]
                     for index, auto_width in enumerate(auto_widths)]
            excess = [0 if isinstance(width, DimBase)
                      else auto_width - max_column_widths[index]
                      for index, auto_width in enumerate(auto_widths)]
            excess_pos = sum(x for x in excess if x > 0)
            extra_neg = sum(x for x in extra if x <= 0) + excess_pos
            extra_pos = (sum(x for x, c in zip(extra, excess)
                             if x > 0 and c <= 0))
            if extra_pos + extra_neg < 0:
                self.warn('Table contents are too wide to fit within the '
                          'available width', container)
                return [width.to_points(container.width)
                        if isinstance(width, DimBase) else width
                        for width in auto_widths]

            def final_column_width(index, width):
                if isinstance(width, DimBase):
                    return width.to_points(container.width)
                elif excess[index] > 0:
                    return max_column_widths[index]
                elif extra[index] <= 0:
                    return min_column_widths[index]
                else:
                    return width + (extra_neg * extra[index] / extra_pos)

            return [final_column_width(i, width)
                    for i, width in enumerate(auto_widths)]
        else:
            return [width.to_points(container.width)
                    for width in column_widths]

    @classmethod
    def _render_section(cls, container, rows, column_widths):
        rendered_rows = []
        rows_left_in_span = 0
        for row in rows:
            rows_left_in_span = max(row.maximum_rowspan, rows_left_in_span) - 1
            rendered_row = cls._render_row(column_widths, container, row)
            rendered_rows.append(rendered_row)
            if rows_left_in_span == 0:
                yield cls._vertically_size_cells(rendered_rows)
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
                container.register_styled(rendered_row.row.section)
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


class TableWithCaption(StaticGroupedFlowables):
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
    section = ReadAliasAttribute('parent')

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
        return next(i for i, item in enumerate(self.section) if item is self)

    def get_rowspanned_columns(self):
        """Return a dictionary mapping column indices to the number of columns
        spanned."""
        spanned_columns = {}
        current_row_index = self._index
        current_row_cols = sum(cell.colspan for cell in self)
        prev_rows = iter(reversed(self.section[:current_row_index]))
        while current_row_cols < self.section.num_columns:
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
    def section(self):
        return self.row.section

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
        return next(i for i, row in enumerate(self.section) if row is self.row)

    def __iter__(self):
        index = int(self)
        return (index + i for i in range(self.cell.rowspan))

    @property
    def num_items(self):
        return len(self.section)


class ColumnIndex(Index):
    def __int__(self):
        spanned_columns = self.row.get_rowspanned_columns()
        column_index = 0
        cells = iter(self.row)
        for col_index in range(self.cell.row.section.num_columns):
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
        return self.row.section.num_columns


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
