# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from itertools import chain

from .draw import Line
from .flowable import Flowable, FlowableState
from .layout import DownExpandingContainer, VirtualContainer, EndOfContainer
from .dimension import PT
from .structure import StaticGroupedFlowables, GroupedFlowablesStyle
from .style import Styled


__all__ = ['Table', 'TableSection', 'TableHead', 'TableBody', 'TableRow',
           'TableCell', 'TableCellStyle', 'TableCellBorder',
           'TOP', 'MIDDLE', 'BOTTOM']


TOP = 'top'
MIDDLE = 'middle'
BOTTOM = 'bottom'


class TableState(FlowableState):
    def __init__(self, rendered_rows, row_index=0):
        super().__init__(row_index == 0)
        self.rendered_rows = rendered_rows
        self.row_index = row_index

    def __copy__(self):
        return self.__class__(self.rendered_rows, self.row_index)


class Table(Flowable):
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
        self._place_cells_and_render_borders(container, state)
        return container.width, 0

    def _render_cells(self, container):
        table_width = float(container.width)
        total_width = sum(self.column_widths)
        column_widths = [table_width * width / total_width
                         for width in self.column_widths]
        rows = iter(self.body.rows)
        num_columns = self.body.rows[0].num_columns
        if self.head:
            rows = chain(iter(self.head.rows), rows)
        rendered_rows = self._render_section(column_widths, container,
                                             num_columns, rows)
        rendered_rows = self._vertically_size_cells(rendered_rows)
        return TableState(rendered_rows)

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
        return rendered_rows

    @staticmethod
    def _render_row(column_widths, container, num_columns, row_idx, row,
                    row_spanned_cells, spanned_cells):
        rendered_row = RenderedRow()
        x_cursor = 0
        cells = iter(row.cells)
        for col_idx in range(num_columns):
            if (row_idx, col_idx) in spanned_cells:
                if (row_idx, col_idx) in row_spanned_cells:
                    x_cursor += row_spanned_cells[row_idx, col_idx].width
                continue
            cell = next(cells)
            cell_width = sum(column_widths[col_idx:col_idx + cell.colspan])
            buffer = VirtualContainer(container, cell_width * PT)
            width, descender = cell.flow(buffer, None)
            rendered_cell = RenderedCell(cell, buffer, x_cursor)
            rendered_row.append(rendered_cell)
            x_cursor += cell_width
            for j in range(col_idx, col_idx + cell.colspan):
                spanned_cells.add((row_idx, j))
            for i in range(row_idx + 1, row_idx + cell.rowspan):
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
    def _place_cells_and_render_borders(container, state):
        """Place the rendered cells onto the page canvas and draw borders around
        them."""
        def draw_cell_border(rendered_cell, cell_height, container):
            for position in ('top', 'right', 'bottom', 'left'):
                border = TableCellBorder(rendered_cell, cell_height, position)
                border.render(container)

        document = container.document
        y_cursor = container.cursor
        row_index = state.row_index
        for r, rendered_row in enumerate(state.rendered_rows[row_index:], row_index):
            try:
                container.advance(rendered_row.height)
            except EndOfContainer:
                state.row_index = r
                raise EndOfContainer(state)
            for c, rendered_cell in enumerate(rendered_row):
                cell_height = sum(row.height for row in
                                  state.rendered_rows[r:r + rendered_cell.rowspan])
                x_cursor = rendered_cell.x_position
                y_pos = float(y_cursor + cell_height)
                border_container = DownExpandingContainer('table cell border',
                                                          container, x_cursor,
                                                          y_pos)
                draw_cell_border(rendered_cell, cell_height, border_container)
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


class TableCellStyle(GroupedFlowablesStyle):
    attributes = {'vertical_align': MIDDLE}


class TableCell(StaticGroupedFlowables):
    style_class = TableCellStyle

    def __init__(self, flowables, rowspan=1, colspan=1,
                 id=None, style=None, parent=None):
        super().__init__(flowables, id=id, style=style, parent=parent)
        self.rowspan = rowspan
        self.colspan = colspan


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
    def __init__(self):
        super().__init__()
        self.height = 0

    def append(self, rendered_cell):
        if rendered_cell.cell.rowspan == 1:
            self.height = max(self.height, rendered_cell.height)
        super().append(rendered_cell)


class TableCellBorder(Line):
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
