
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
        for r, row in enumerate(self.data):
            rendered_row = []
            x_cursor = 0
            row_height = 0
            for c, cell in enumerate(row):
                buffer = canvas.new(x_cursor, 0, column_width,
                                    canvas.height - y_cursor)
                cell_style = self.cell_styles[r][c]
                cell_height = self.render_cell(cell, buffer, cell_style)
                x_cursor += column_width
                row_height = max(row_height, cell_height)
                rendered_row.append((buffer, cell_height))
            x_cursor = 0
            for c, (buffer, height) in enumerate(rendered_row):
                border_buffer = canvas.append_new(x_cursor,
                                                  canvas.height - y_cursor - row_height,
                                                  column_width, row_height)
                cell_style = self.cell_styles[r][c]
                self.draw_cell_border(border_buffer, row_height, cell_style)
                if cell_style.vertical_align == MIDDLE:
                    vertical_offset = (row_height - height) / 2
                elif cell_style.vertical_align == BOTTOM:
                    vertical_offset = (row_height - height)
                else:
                    vertical_offset = 0
                if vertical_offset:
                    canvas.save_state()
                    canvas.translate(0, - vertical_offset)
                    canvas.append(buffer)
                    canvas.restore_state()
                else:
                    canvas.append(buffer)
                x_cursor += column_width
            y_cursor += row_height
        return y_cursor - offset

    def render_cell(self, cell, canvas, style):
        if cell.content:
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


class TabularRow(list):
    def __init__(self, items):
        super().__init__(items)


class TabularData(Array):
    pass


class HTMLTabularData(TabularData):
    def __init__(self, element):
        rows = []
        for tr in element.tr:
            row_cells = []
            for cell in tr.getchildren():
                row_cells.append(TabularCell(cell.text))
                print(cell.text)
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
