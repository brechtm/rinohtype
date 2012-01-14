
import csv

from copy import copy

from .draw import Line
from .flowable import Flowable, FlowableStyle
from .paragraph import Paragraph, ParagraphStyle
from .style import Style
from .unit import pt


class CellStyle(ParagraphStyle):
    attributes = {'top_border': None,
                  'right_border': None,
                  'bottom_border': None,
                  'left_border': None}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class TabularStyle(CellStyle):
    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)
        self.cell_style = []

    def set_cell_style(self, style, rows=slice(None), cols=slice(None)):
        self.cell_style.append(((rows, cols), style))
        style.base = self


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
        column_width = table_width / self.data.columns
        y_cursor = offset
        for r, rows in enumerate(self.data):
            x_cursor = 0
            row_height = 0
            for c, cell in enumerate(rows):
                buffer = canvas.append_new(x_cursor, 0, column_width,
                                           canvas.height - y_cursor)
                cell_style = self.cell_styles[r][c]
                cell_height = self.render_cell(cell, buffer, cell_style)
                x_cursor += column_width
                row_height = max(row_height, cell_height)
            y_cursor += row_height
        return y_cursor - offset

    def render_cell(self, cell, canvas, style):
        cell_par = Paragraph(cell.content, style=style)
        return cell_par.render(canvas)


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


class TabularRow(list):
    def __init__(self, items):
        super().__init__(items)


class TabularData(Array):
    pass

class CSVTabularData(TabularData):
    def __init__(self, filename):
        rows = []
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                row_cells = [TabularCell(cell) for cell in row]
                rows.append(TabularRow(row_cells))
        super().__init__(rows)
