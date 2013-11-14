# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import unicodedata

from copy import copy
from itertools import chain, tee

from .layout import EndOfContainer, MaybeContainer
from .flowable import Flowable, FlowableState
from .number import format_number, NUMBER
from .paragraph import ParagraphStyle, Paragraph, TabStop, RIGHT
from .reference import Reference, Referenceable, REFERENCE, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, FixedWidthSpace, Tab
from .dimension import PT
from .style import PARENT_STYLE


__all__ = ['HeadingStyle', 'Heading', 'ListStyle', 'List',
           'DefinitionListStyle', 'DefinitionList',
           'HeaderStyle', 'Header', 'FooterStyle', 'Footer',
           'TableOfContentsStyle', 'TableOfContents']


class HeadingStyle(ParagraphStyle):
    attributes = {'numbering_style': NUMBER,
                  'numbering_separator': '.'}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


# TODO: share superclass with List (numbering)
class Heading(Paragraph, Referenceable):
    style_class = HeadingStyle

    def __init__(self, document, title, style=None, level=1, id=None):
        self._title = title
        counters = document.counters.setdefault(self.__class__, {1: 1})
        if style.numbering_style is not None:
            self.number = format_number(counters[level], style.numbering_style)
            number = self.number + style.numbering_separator + FixedWidthSpace()
            counters[level] += 1
            counters[level + 1] = 1
        else:
            self.number = None
            number = ''
        self.level = level
        if id is None:
            id = document.unique_id
        Paragraph.__init__(self, number + title, style)
        Referenceable.__init__(self, document, id)

    def reference(self):
        return self.number

    def title(self):
        return self._title

    def render(self, container, last_descender, state=None):
        if self.level == 1:
            container.page.section = self
        self.update_page_reference(container.page)
        return super().render(container, last_descender, state=state)


class ListStyle(ParagraphStyle):
    attributes = {'ordered': False,
                  'bullet': SingleStyledText('\N{BULLET}'),
                  'item_indent': 12*PT,
                  'item_spacing': 0*PT,
                  'numbering_style': NUMBER,
                  'numbering_separator': ')'}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class ListState(FlowableState):
    def __init__(self, list_items, current_list_item_state=None):
        self.list_items = list_items
        self.current_list_item_state = current_list_item_state

    def __copy__(self):
        copy_list_items, self.list_items = tee(self.list_items)
        copy_current_list_item_state = copy(self.current_list_item_state)
        return self.__class__(copy_list_items, copy_current_list_item_state)

    def next_list_item(self):
        return next(self.list_items)

    def prepend_list_item(self, list_item):
        self.list_items = chain((list_item, ), self.list_items)


class List(Flowable, list):
    style_class = ListStyle

    def __init__(self, items, style=None):
        super().__init__(style)
        # TODO: replace item styles with custom render method
        item_style = ListStyle(space_above=0*PT,
                               space_below=self.style.item_spacing,
                               base=style)
        last_item_style = ListStyle(space_above=0*PT, space_below=0*PT,
                                    base=style)
        if style.ordered:
            separator = style.numbering_separator
            numbers = [format_number(i + 1, self.get_style('numbering_style'))
                       for i in range(len(items))]
        else:
            separator = ''
            numbers = [style.bullet] * len(items)
        for i, item in enumerate(items[:-1]):
            item = ListItem(numbers[i], separator, item, style=item_style,
                            parent=self)
            self.append(item)
        last = ListItem(numbers[-1], separator, items[-1],
                        style=last_item_style, parent=self)
        self.append(last)

    def render(self, container, descender, state=None):
        state = state or ListState(iter(self), None)

        try:
            while True:
                list_item = state.next_list_item()
                _, descender = list_item.flow(container, descender,
                                              state=state.current_list_item_state)
                state.current_list_item_state = None
        except EndOfContainer as eoc:
            state.prepend_list_item(list_item)
            state.current_list_item_state = eoc.flowable_state
            raise EndOfContainer(state)
        except StopIteration:
            pass


class ListItemNumber(Paragraph):
    def render(self, container, descender, state=None):
        before = container.cursor
        result = super().render(container, descender, state=state)
        container.advance(before - container.cursor)
        return result


class ListItem(Flowable):
    def __init__(self, number, separator, flowables, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        tab_stop = TabStop(self.get_style('item_indent'), align=RIGHT)
        marker_style = ParagraphStyle(base=style, tab_stops=[tab_stop])
        self.marker = ListItemNumber([Tab() + number + separator],
                                     style=marker_style)
        self.flowables = flowables

    def render(self, container, last_descender, state=None):
        if not state:
            maybe_container = MaybeContainer(container)
            height, _ = self.marker.flow(maybe_container, last_descender)
            try:
                flowables_iterator = iter(self.flowables)
                first_flowable = next(flowables_iterator)
                height, last_descender = first_flowable.flow(maybe_container,
                                                             last_descender)
                state = ListItemState(flowables_iterator)
                maybe_container.do_place()
            except EndOfContainer as e:
                if e.flowable_state:
                    maybe_container.do_place()
                    state = ListItemState(flowables_iterator, e.flowable_state)
                    state.prepend(first_flowable)
                raise EndOfContainer(state)
        for flowable in state.flowable_iterator:
            try:
                height, last_descender = flowable.flow(container,
                                                       last_descender,
                                                       state.flowable_state)
                state.flowable_state = None
            except EndOfContainer as e:
                state.prepend(flowable)
                state.flowable_state = e.flowable_state
                raise EndOfContainer(state)
        return last_descender


class ListItemState(FlowableState):
    def __init__(self, flowable_iterator, flowable_state=None):
        self.flowable_iterator = flowable_iterator
        self.flowable_state = flowable_state

    def __copy__(self):
        self.flowable_iterator, copy_iterator = tee(self.flowable_iterator)
        return self.__class__(copy_iterator, copy(self.flowable_state))

    def prepend(self, flowable):
        self.flowable_iterator = chain((flowable, ), self.flowable_iterator)



class DefinitionListStyle(ParagraphStyle):
    attributes = {'term_style': PARENT_STYLE,
                  'item_spacing': 0*PT,
                  'indentation': 10*PT}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class DefinitionList(Paragraph):
    style_class = DefinitionListStyle

    def __init__(self, items, style=None):
        super().__init__([], style)
        term_style = self.style.term_style
        term_style = ParagraphStyle(space_above=0*PT,
                                    space_below=0*PT,
                                    base=style)
        definition_style = ParagraphStyle(space_above=0*PT,
                                          space_below=self.style.item_spacing,
                                          indent_left=self.style.indentation,
                                          base=style)
        last_definition_style = ParagraphStyle(space_above=0*PT,
                                               space_below=0*PT,
                                               indent_left=self.style.indentation,
                                               base=style)
        for i, item in enumerate(items[:-1]):
            term, definition = item
            term_par = Paragraph(term, style=term_style)
            definition_par =  Paragraph(definition, style=definition_style)
            term_par.parent = definition_par.parent = self
            self.append(term_par)
            self.append(definition_par)
        last_term, last_definition = items[-1]
        last_term_par = Paragraph(last_term, style=term_style)
        last_definition_par = Paragraph(last_definition,
                                        style=last_definition_style)
        last_term_par.parent = last_definition_par.parent = self
        self.append(last_term_par)
        self.append(last_definition_par)


class HeaderStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Header(Paragraph):
    style_class = HeaderStyle

    def __init__(self, style=None):
        super().__init__([], style)

    def render(self, container, last_descender, state=None):
        text = Variable(SECTION_NUMBER) + ' ' + Variable(SECTION_TITLE)
        text.parent = self
        self.append(text)
        return super().render(container, last_descender, state=state)


class FooterStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Footer(Paragraph):
    style_class = FooterStyle

    def __init__(self, style=None):
        super().__init__([], style)

    def render(self, container, last_descender, state=None):
        text = Variable(PAGE_NUMBER) + ' / ' + Variable(NUMBER_OF_PAGES)
        text.parent = self
        self.append(text)
        return super().render(container, last_descender, state=state)


class TableOfContentsStyle(ParagraphStyle):
    attributes = {'depth': 3}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TableOfContents(Paragraph):
    style_class = TableOfContentsStyle
    location = 'table of contents'

    def __init__(self, style=None, styles=[]):
        super().__init__([], style)
        self.styles = styles

    def register(self, flowable):
        if (isinstance(flowable, Heading) and
            flowable.level <= self.get_style('depth')):
            text = [Reference(flowable.id, type=REFERENCE), Tab(),
                    Reference(flowable.id, type=TITLE), Tab(),
                    Reference(flowable.id, type=PAGE)]
            for reference in text:
                reference.source = self
            try:
                style_index = flowable.level - 1
                flowable = Paragraph(text, style=self.styles[style_index])
            except AttributeError:
                flowable = Paragraph(text, style=self.styles[-1])
            flowable.parent = self
            self.append(flowable)
