# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from collections import Iterable
from itertools import chain
from functools import partial
from math import sqrt

from .draw import Line, Rectangle, ShapeStyle
from .flowable import Flowable, FlowableStyle, FlowableState
from .layout import MaybeContainer, VirtualContainer, EndOfContainer
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
    def __init__(self, column_widths, body_row_index=0):
        super().__init__()
        self.column_widths = column_widths
        self.body_row_index = body_row_index

    @property
    def body_row_index(self):
        return self._body_row_index

    @body_row_index.setter
    def body_row_index(self, body_row_index):
        self._body_row_index = body_row_index
        self.initial = body_row_index == 0

    def __copy__(self):
        return self.__class__(self.column_widths, self.body_row_index)


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
        get_style = partial(self.get_style, document=container.document)
        state = state or TableState(self._size_columns(container))
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
        return sum(state.column_widths), 0

    def _size_columns(self, container):
        """Calculate the table's column sizes constrained by:

        - requested relative widths
        - container width (= available width)
        - cell contents

        """
        def calculate_column_widths(max_cell_width):
            """Calculate required column widths given a maximum cell width"""
            def cell_content_width(cell):
                buffer = VirtualContainer(container, width=max_cell_width)
                width, _ = cell.flow(buffer, None)
                return float(width)

            widths = [0] * self.body[0].num_columns
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

        max_column_widths = calculate_column_widths(float('+inf'))
        if sum(max_column_widths) < container.width:
            if self.column_widths:
                factor = max(maximum / required for maximum, required
                             in zip(max_column_widths, self.column_widths))
                if sum(self.column_widths) * factor < container.width:
                    return [width * factor for width in self.column_widths]
            else:
                return max_column_widths
        # this point is reached when the table cannot fit the available width
        # without line-wrapping the cells' contents
        if self.column_widths:
            rel_column_widths = self.column_widths
        else:   # automatically choose the relative column widths
            min_column_widths = calculate_column_widths(0)
            rel_column_widths = [sqrt(minimum * maximum) for minimum, maximum
                                 in zip(min_column_widths, max_column_widths)]
        scale = float(container.width) / sum(rel_column_widths)
        return [width * scale for width in rel_column_widths]

    @classmethod
    def _render_section(cls, container, rows, column_widths):
        spanned_cells = set()
        row_spanned_cells = {}
        rendered_rows = []
        rows_left_in_span = 0
        for row in rows:
            rows_left_in_span = max(row.maximum_rowspan, rows_left_in_span) - 1
            rendered_row = cls._render_row(column_widths, container, row,
                                           row_spanned_cells, spanned_cells)
            rendered_rows.append(rendered_row)
            if rows_left_in_span == 0:
                yield cls._vertically_size_cells(rendered_rows)
                rendered_rows = []
        assert not rendered_rows

    @staticmethod
    def _render_row(column_widths, container, row,
                    row_spanned_cells, spanned_cells):
        num_columns = sum(cell.colspan for cell in row)
        row_index = int(row.index)
        rendered_row = RenderedRow(row_index, row)
        x_cursor = 0
        cells = iter(row)
        for col_idx in range(num_columns):
            if (row_index, col_idx) in spanned_cells:
                if (row_index, col_idx) in row_spanned_cells:
                    x_cursor += row_spanned_cells[row_index, col_idx].width
                continue
            cell = next(cells)
            cell_width = sum(column_widths[col_idx:col_idx + cell.colspan])
            buffer = VirtualContainer(container, cell_width)
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

        document = container.document
        y_cursor = container.cursor
        for r, rendered_row in enumerate(rendered_rows):
            container.advance(rendered_row.height)
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


class TableSection(Styled, list):
    def __init__(self, rows, style=None, parent=None):
        Styled.__init__(self, style=style, parent=parent)
        list.__init__(self, rows)
        for row in rows:
            row.parent = self

    def prepare(self, document):
        for row in self:
            row.prepare(document)


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
    def num_columns(self):
        return sum(cell.colspan for cell in self)

    @property
    def maximum_rowspan(self):
        return max(cell.rowspan for cell in self)

    def prepare(self, document):
        for cells in self:
            cells.prepare(document)

    @property
    def index(self):
        return RowIndex(self)


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
        return ColumnIndex(self)


class Index(object):
    def __init__(self, element):
        self.element = element

    @property
    def parent(self):
        return self.element.parent

    def __int__(self):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, slice):
            elements = self.parent[other]
        elif isinstance(other, Iterable):
            elements = (self.parent[index] for index in other)
        else:
            elements = (self.parent[other], )
        return any(self.element is elem for elem in elements)


class RowIndex(Index):
    def __int__(self):
        for row_index, row in enumerate(self.parent):
            if row is self.element:
                return row_index


class ColumnIndex(Index):
    def __int__(self):
        column_index = 0
        for cell in self.parent:
            if cell is self.element:
                return column_index
            column_index += cell.colspan


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
