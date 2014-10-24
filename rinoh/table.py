# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections import Iterable
from functools import partial

from .draw import Line, Rectangle, ShapeStyle
from .flowable import Flowable, FlowableStyle, FlowableState
from .layout import MaybeContainer, VirtualContainer, EndOfContainer
from .dimension import PT
from .structure import StaticGroupedFlowables, GroupedFlowablesStyle
from .style import Styled


__all__ = ['Table', 'TableSection', 'TableHead', 'TableBody', 'TableRow',
           'TableCell', 'TableCellStyle', 'TableCellBorder',
           'TableCellBackground',
           'TOP', 'MIDDLE', 'BOTTOM']


TOP = 'top'
MIDDLE = 'middle'
BOTTOM = 'bottom'


class TableState(FlowableState):
    def __init__(self, head_rows, body_rows, row_index=0):
        super().__init__(row_index == 0)
        self.head_rows = head_rows
        self.body_rows = body_rows
        self.row_index = row_index

    def __copy__(self):
        return self.__class__(self.head_rows, self.body_rows, self.row_index)


class TableStyle(FlowableStyle):
    attributes = {'split_minimum_rows': 5,
                  'repeat_head': False}


NEVER_SPLIT = float('+inf')


class Table(Flowable):
    style_class = TableStyle

    def __init__(self, body, head=None, column_widths=None,
                 id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.head = head
        if head:
            head.parent = self
        self.body = body
        body.parent = self
        self.column_widths = column_widths

    def render(self, container, last_descender, state=None):
        # TODO: allow data to override style (align)
        state = state or self._render_cells(container)
        # TODO: if on new page, rerender rows (needed if PAGE_NUMBER Field used)
        get_style = partial(self.get_style, document=container.document)
        with MaybeContainer(container) as maybe_container:
            if self.head and (state.initial or get_style('repeat_head')):
                self._place_cells_and_render_borders(maybe_container,
                                                     state.head_rows)
            try:
                self._place_cells_and_render_borders(maybe_container,
                                                     state.body_rows,
                                                     state.row_index)
            except EndOfContainer as e:
                rows_set = e.flowable_state
                rows_left = len(self.body.rows) - rows_set
                if min(rows_set, rows_left) >= get_style('split_minimum_rows'):
                    state.row_index = rows_set
                    state.initial = rows_set == 0
                raise EndOfContainer(state)
        return container.width, 0

    def _render_cells(self, container):
        table_width = float(container.width)
        total_width = sum(self.column_widths)
        column_widths = [table_width * width / total_width
                         for width in self.column_widths]
        num_columns = self.body.rows[0].num_columns
        head_rows = (self._render_section(column_widths, container, num_columns,
                                          self.head.rows)
                     if self.head else None)
        body_rows = self._render_section(column_widths, container, num_columns,
                                         self.body.rows)
        return TableState(head_rows, body_rows)

    @classmethod
    def _render_section(cls, column_widths, container, num_columns, rows):
        spanned_cells = set()
        row_spanned_cells = {}
        rendered_rows = []
        for r, row in enumerate(rows):
            rendered_row = cls._render_row(column_widths, container,
                                           num_columns, r, row,
                                           row_spanned_cells, spanned_cells)
            rendered_rows.append(rendered_row)
        rendered_rows = cls._vertically_size_cells(rendered_rows)
        return rendered_rows

    @staticmethod
    def _render_row(column_widths, container, num_columns, row_index, row,
                    row_spanned_cells, spanned_cells):
        rendered_row = RenderedRow(row_index, row)
        x_cursor = 0
        cells = iter(row.cells)
        for col_idx in range(num_columns):
            if (row_index, col_idx) in spanned_cells:
                if (row_index, col_idx) in row_spanned_cells:
                    x_cursor += row_spanned_cells[row_index, col_idx].width
                continue
            cell = next(cells)
            cell_width = sum(column_widths[col_idx:col_idx + cell.colspan])
            buffer = VirtualContainer(container, cell_width * PT)
            width, descender = cell.flow(buffer, None)
            rendered_cell = RenderedCell(cell, buffer, x_cursor)
            rendered_row.append(rendered_cell)
            x_cursor += cell_width
            for j in range(col_idx, col_idx + cell.colspan):
                spanned_cells.add((row_index, j))
            for i in range(row_index + 1, row_index + cell.rowspan):
                row_spanned_cells[i, col_idx] = rendered_cell
                for j in range(col_idx, col_idx + cell.colspan):
                    spanned_cells.add((i, j))
        return rendered_row

    @staticmethod
    def _vertically_size_cells(rendered_rows):
        """Grow row heights to cater for vertically spanned cells that do not
        fit in the available space."""
        for r, rendered_row in enumerate(rendered_rows):
            for c, rendered_cell in enumerate(rendered_row):
                if rendered_cell.rowspan > 1:
                    row_height = sum(row.height for row in
                                     rendered_rows[r:r + rendered_cell.rowspan])
                    shortage = rendered_cell.height - row_height
                    if shortage > 0:
                        padding = shortage / rendered_cell.rowspan
                        for i in range(r, r + rendered_cell.rowspan):
                            rendered_rows[i].height += padding
        return rendered_rows

    @staticmethod
    def _place_cells_and_render_borders(container, rendered_rows, row_index=0):
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

        document = container.document
        y_cursor = container.cursor
        for r, rendered_row in enumerate(rendered_rows[row_index:], row_index):
            try:
                container.advance(rendered_row.height)
            except EndOfContainer:
                raise EndOfContainer(r)
            for c, rendered_cell in enumerate(rendered_row):
                cell_height = sum(rendered_row.height for rendered_row in
                                  rendered_rows[r:r + rendered_cell.rowspan])
                x_cursor = rendered_cell.x_position
                y_pos = float(y_cursor + cell_height)
                cell_container = VirtualContainer(container)
                draw_cell_border(rendered_cell, cell_height, cell_container)
                cell_container.place_at(container, x_cursor, y_pos)
                vertical_align = rendered_cell.cell.get_style('vertical_align',
                                                              document)
                if vertical_align == TOP:
                    vertical_offset = 0
                elif vertical_align == MIDDLE:
                    vertical_offset = (cell_height - rendered_cell.height) / 2
                elif vertical_align == BOTTOM:
                    vertical_offset = (cell_height - rendered_cell.height)
                y_offset = float(y_cursor + vertical_offset)
                rendered_cell.container.place_at(container, x_cursor, y_offset)
            y_cursor += rendered_row.height


class TableSection(Styled):
    def __init__(self, rows, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.rows = rows
        for row in rows:
            row.parent = self

    def prepare(self, document):
        for row in self.rows:
            row.prepare(document)


class TableHead(TableSection):
    pass


class TableBody(TableSection):
    pass


class TableRow(Styled):
    def __init__(self, cells, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.cells = cells
        for cell in cells:
            cell.parent = self

    @property
    def num_columns(self):
        return sum(cell.colspan for cell in self.cells)

    def prepare(self, document):
        for cells in self.cells:
            cells.prepare(document)

    @property
    def index(self):
        for row_index, row in enumerate(self.parent.rows):
            if row is self:
                return Index(row_index, len(self.parent.rows))


class TableCellStyle(GroupedFlowablesStyle):
    attributes = {'vertical_align': MIDDLE,
                  'background_color': None}


class TableCell(StaticGroupedFlowables):
    style_class = TableCellStyle

    def __init__(self, flowables, rowspan=1, colspan=1,
                 id=None, style=None, parent=None):
        super().__init__(flowables, id=id, style=style, parent=parent)
        self.rowspan = rowspan
        self.colspan = colspan

    @property
    def row_index(self):
        return self.parent.index

    @property
    def column_index(self):
        column_index = 0
        for cell in self.parent.cells:
            if cell is self:
                return Index(column_index, self.parent.num_columns)
            column_index += cell.colspan


class Index(object):
    def __init__(self, index, length):
        self.index = index
        self.length = length

    def __eq__(self, indices):
        if isinstance(indices, slice):
            return self.index in range(*indices.indices(self.length))
        elif isinstance(indices, Iterable):
            return self.index in (index if index > 0 else index + self.length
                                  for index in indices)
        else:
            if indices < 0:
                indices += self.length
            return indices == self.index


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


class TableCellBorderStyle(ShapeStyle):
    attributes = {'stroke_width': None}


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
    attributes = {'fill_color': None,
                  'stroke_color': None}


class TableCellBackground(Rectangle):
    style_class = TableCellBackgroundStyle
