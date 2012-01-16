
import csv

from copy import copy

from .draw import Line
from .flowable import Flowable, FlowableStyle
from .paragraph import Paragraph, ParagraphStyle
from .style import Style
from .unit import pt


TOP = 'top'
MIDDLE = 'middle'
BOTTOM = 'bottom'


class CellStyle(ParagraphStyle):
    attributes = {'top_border': None,
                  'right_border': None,
                  'bottom_border': None,
                  'left_border': None,
                  'vertical_align': MIDDLE}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class TabularStyle(CellStyle):
    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)
        self.cell_style = []

    def set_cell_style(self, style, rows=slice(None), cols=slice(None)):
        self.cell_style.append(((rows, cols), style))
        style.base = self


class RenderedCell(object):
    def __init__(self, cell, canvas, x_position, height):
        self.cell = cell
        self.canvas = canvas
        self.x_position = x_position
        self.height = height

    @property
    def width(self):
        return self.canvas.width

    @property
    def rowspan(self):
        return self.cell.rowspan


class Tabular(Flowable):
    style_class = TabularStyle

    def __init__(self, data, style=None):
        super().__init__(style=style)
        self.data = data
        self.cell_styles = Array([[style for c in range(self.data.columns)]
                                  for r in range(self.data.rows)])
        for (row_slice, col_slice), style in self.style.cell_style:
            if isinstance(row_slice, int):
                row_range = [row_slice]
            else:
                row_indices = row_slice.indices(self.cell_styles.rows)
                row_range = range(*row_indices)
            for ri in row_range:
                if isinstance(col_slice, int):
                    col_range = [col_slice]
                else:
                    col_indices = col_slice.indices(self.cell_styles.columns)
                    col_range = range(*col_indices)
                for ci in col_range:
                    old_style = self.cell_styles[ri][ci]
                    self.cell_styles[ri][ci] = copy(style)
                    self.cell_styles[ri][ci].base = old_style

    def render(self, canvas, offset=0):
        table_width = canvas.width
        row_heights = []
        rendered_rows = []

        # render cell content
        row_spanned_cells = {}
        column_width = table_width / self.data.columns
        for r, row in enumerate(self.data):
            rendered_row = []
            x_cursor = 0
            row_height = 0
            for c, cell in enumerate(row):
                if (r, c) in row_spanned_cells:
                    x_cursor += row_spanned_cells[r, c].width
                    continue
                elif cell is None:
                    continue
                cell_width = column_width * cell.colspan
                buffer = canvas.new(x_cursor, 0, cell_width, canvas.height)
                cell_style = self.cell_styles[r][c]
                cell_height = self.render_cell(cell, buffer, cell_style)
                if cell.rowspan == 1:
                    row_height = max(row_height, cell_height)
                rendered_cell = RenderedCell(cell, buffer, x_cursor,
                                             cell_height)
                rendered_row.append(rendered_cell)
                x_cursor += cell_width
                for i in range(r + 1, r + cell.rowspan):
                    row_spanned_cells[i, c] = rendered_cell
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

        # place cell content and render cell border
        y_cursor = offset
        for r, rendered_row in enumerate(rendered_rows):
            for c, rendered_cell in enumerate(rendered_row):
                if rendered_cell.rowspan > 1:
                    row_height = sum(row_heights[r:r + rendered_cell.rowspan])
                else:
                    row_height = row_heights[r]
                x_cursor = rendered_cell.x_position
                cell_height = canvas.height - y_cursor - row_height
                cell_width = rendered_cell.width
                border_buffer = canvas.append_new(x_cursor, cell_height,
                                                  cell_width, row_height)
                cell_style = self.cell_styles[r][c]
                self.draw_cell_border(border_buffer, row_height, cell_style)
                if cell_style.vertical_align == MIDDLE:
                    vertical_offset = (row_height - rendered_cell.height) / 2
                elif cell_style.vertical_align == BOTTOM:
                    vertical_offset = (row_height - rendered_cell.height)
                else:
                    vertical_offset = 0
                canvas.save_state()
                canvas.translate(0, - (y_cursor + vertical_offset))
                canvas.append(rendered_cell.canvas)
                canvas.restore_state()
            y_cursor += row_height
        return y_cursor - offset

    def render_cell(self, cell, canvas, style):
        if cell is not None and cell.content:
            cell_par = Paragraph(cell.content, style=style)
            return cell_par.render(canvas)
        else:
            return 0

    def draw_cell_border(self, canvas, height, style):
        left, bottom, right, top = 0, 0, canvas.width, canvas.height
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


class Array(list):
    def __init__(self, rows):
        super().__init__(rows)

    @property
    def rows(self):
        return len(self)

    @property
    def columns(self):
        return len(self[0])


class TabularCell(object):
    def __init__(self, content, rowspan=1, colspan=1):
        self.content = content
        self.rowspan = rowspan
        self.colspan = colspan

    def __repr__(self):
        if self.content is not None:
            return self.content
        else:
            return '<empty>'


class TabularRow(list):
    def __init__(self, items):
        super().__init__(items)


class TabularData(Array):
    pass


class HTMLTabularData(TabularData):
    def __init__(self, element):
        rows = []
        spanned_cells = []
        for r, tr in enumerate(element.tr):
            row_cells = []
            cells = tr.getchildren()
            index = c = 0
            while index < len(cells):
                if (r, c) in spanned_cells:
                    cell = None
                else:
                    rowspan = int(cells[index].get('rowspan', 1))
                    colspan = int(cells[index].get('colspan', 1))
                    cell = TabularCell(cells[index].text, rowspan, colspan)
                    if rowspan > 1 or colspan > 1:
                        for j in range(c, c + colspan):
                            for i in range(r, r + rowspan):
                                spanned_cells.append((i, j))
                    index += 1
                row_cells.append(cell)
                c += 1
            rows.append(TabularRow(row_cells))
        super().__init__(rows)


class CSVTabularData(TabularData):
    def __init__(self, filename):
        rows = []
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                row_cells = [TabularCell(cell) for cell in row]
                rows.append(TabularRow(row_cells))
        super().__init__(rows)
