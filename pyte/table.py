
import csv


from .flowable import Flowable, FlowableStyle
from .paragraph import Paragraph, ParagraphStyle
from .unit import pt


class TabularStyle(ParagraphStyle):
    attributes = {'lineThickness': 2*pt}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Tabular(Flowable):
    style_class = TabularStyle

    def __init__(self, data, style=None):
        super().__init__(style=style)
        self.data = data

    def render(self, canvas, offset=0):
        table_width = canvas.width
        column_width = table_width / self.data.columns
        y_cursor = offset
        for rows in self.data:
            x_cursor = 0
            row_height = 0
            for cell in rows:
                buffer = canvas.append_new(x_cursor, 0, column_width,
                                           canvas.height - y_cursor)
                cell_height = self.render_cell(cell, buffer)
                x_cursor += column_width
                row_height = max(row_height, cell_height)
            y_cursor += row_height
        return y_cursor - offset

    def render_cell(self, cell, canvas):
        cell_par = Paragraph(cell.content, style=self.style)
        return cell_par.render(canvas)


class TabularCell(object):
    def __init__(self, content, rowspan=1, colspan=1):
        self.content = content
        self.rowspan = rowspan
        self.colspan = colspan


class TabularRow(list):
    def __init__(self, items):
        super().__init__(items)


class TabularData(list):
    def __init__(self, rows):
        super().__init__(rows)

    @property
    def rows(self):
        return len(self[0])

    @property
    def columns(self):
        return len(self)


class CSVTabularData(TabularData):
    def __init__(self, filename):
        rows = []
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                row_cells = [TabularCell(cell) for cell in row]
                rows.append(TabularRow(row_cells))
        super().__init__(rows)
