# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from itertools import chain

from .draw import Line
from .flowable import Flowable
from .layout import VirtualContainer
from .dimension import PT
from .structure import StaticGroupedFlowables, GroupedFlowablesStyle
from .style import Styled


__all__ = ['Table', 'TableHead', 'TableBody', 'TableRow',
           'TableCell', 'TableCellStyle', 'TOP', 'MIDDLE', 'BOTTOM']


TOP = 'top'
MIDDLE = 'middle'
BOTTOM = 'bottom'


class Table(Flowable):
    def __init__(self, head, body, column_widths=None,
                 id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.head = head
        self.body = body
        head.parent = body.parent = self
        self.column_widths = column_widths

    def render(self, container, last_descender, state=None):
        # TODO: allow data to override style (align)
        doc = container.document
        canvas = container.canvas
        table_width = float(container.width)
        row_heights = []
        rendered_rows = []

        num_columns = self.head.rows[0].num_columns

        # calculate column widths (static)
        total_width = sum(self.column_widths)
        column_widths = [table_width * width / total_width
                         for width in self.column_widths]

        # render cell content
        spanned_cells = set()
        row_spanned_cells = {}
        rows = chain(iter(self.head.rows), iter(self.body.rows))
        for r, row in enumerate(rows):
            rendered_row = []
            x_cursor = 0
            row_height = 0
            cells = iter(row.cells)
            for c in range(num_columns):
                if (r, c) in spanned_cells:
                    if (r, c) in row_spanned_cells:
                        x_cursor += row_spanned_cells[r, c].width
                    continue
                cell = next(cells)
                cell_width = sum(column_widths[i]
                                 for i in range(c, c + cell.colspan))
                buffer = VirtualContainer(container, cell_width*PT)
                width, descender = cell.flow(buffer, None)
                rendered_cell = RenderedCell(cell, buffer, x_cursor)
                rendered_row.append(rendered_cell)
                if cell.rowspan == 1:
                    row_height = max(row_height, rendered_cell.height)
                x_cursor += cell_width
                for j in range(c, c + cell.colspan):
                    spanned_cells.add((r, j))
                for i in range(r + 1, r + cell.rowspan):
                    row_spanned_cells[i, c] = rendered_cell
                    for j in range(c, c + cell.colspan):
                        spanned_cells.add((i, j))
            row_heights.append(row_height)
            rendered_rows.append(rendered_row)

        # handle oversized vertically spanned cells
        for r, rendered_row in enumerate(rendered_rows):
            for c, rendered_cell in enumerate(rendered_row):
                if rendered_cell.rowspan > 1:
                    row_height = sum(row_heights[r:r + rendered_cell.rowspan])
                    shortage = rendered_cell.height - row_height
                    if shortage > 0:
                        padding = shortage / rendered_cell.rowspan
                        for i in range(r, r + rendered_cell.rowspan):
                            row_heights[i] += padding

        y_cursor = container.cursor
        table_height = sum(row_heights)
        container.advance(table_height)

        # place cell content and render cell border
        for r, rendered_row in enumerate(rendered_rows):
            for c, rendered_cell in enumerate(rendered_row):
                if rendered_cell.rowspan > 1:
                    cell_height = sum(row_heights[r:r + rendered_cell.rowspan])
                else:
                    cell_height = row_heights[r]
                x_cursor = rendered_cell.x_position
                y_pos = float(y_cursor + cell_height)
                cell_width = rendered_cell.width
                border_buffer = canvas.new()
                # cell_style = cell_styles[r][c]
                # self.draw_cell_border(border_buffer, cell_width, cell_height,
                #                       cell_style)
                border_buffer.append(x_cursor, y_pos)
                vertical_align = cell.get_style('vertical_align', doc)
                if vertical_align == MIDDLE:
                    vertical_offset = (cell_height - rendered_cell.height) / 2
                elif vertical_align:
                    vertical_offset = (cell_height - rendered_cell.height)
                else:
                    vertical_offset = 0
                y_offset = float(y_cursor + vertical_offset)
                rendered_cell.container.place_at(x_cursor, y_offset)
            y_cursor += row_heights[r]
        return container.width, 0

    def draw_cell_border(self, canvas, width, height, style):
        left, bottom, right, top = 0, 0, width, height
        if style.top_border:
            line = Line((left, top), (right, top), style.top_border)
            line.render(canvas)
        if style.right_border:
            line = Line((right, top), (right, bottom), style.right_border)
            line.render(canvas)
        if style.bottom_border:
            line = Line((left, bottom), (right, bottom), style.bottom_border)
            line.render(canvas)
        if style.left_border:
            line = Line((left, bottom), (left, top), style.left_border)
            line.render(canvas)


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
