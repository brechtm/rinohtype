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
from .flowable import Flowable, FlowableState, GroupedFlowables
from .number import format_number, NUMBER
from .paragraph import ParagraphStyle, ParagraphBase, Paragraph, ParagraphState
from .paragraph import TabStop, RIGHT
from .reference import Reference, Referenceable, REFERENCE, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, MixedStyledText, FixedWidthSpace, Tab
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
class Heading(Referenceable, ParagraphBase):
    style_class = HeadingStyle

    def __init__(self, title, style=None, level=1, id=None):
        ParagraphBase.__init__(self, style)
        Referenceable.__init__(self, id)
        self.title = title
        self.level = level

    def prepare(self, document):
        super().prepare(document)
        element_id = self.get_id(document)
        heading_counters = document.counters.setdefault(__class__, {})
        level_counter = heading_counters.setdefault(self.level, [])
        level_counter.append(self)

        number = 0
        for element in document.counters[__class__][self.level]:
            if element.get_style('numbering_style', document) is not None:
                number += 1
            if element is self:
                break
        numbering_style = self.get_style('numbering_style', document)
        if numbering_style is not None:
            formatted_number = format_number(number, numbering_style)
        else:
            formatted_number = ''
        document.set_reference(element_id, REFERENCE, formatted_number)
        document.set_reference(element_id, TITLE, self.title)

    def spans(self, document):
        numbering_style = self.get_style('numbering_style', document)
        if numbering_style is not None:
            formatted_number = Reference(self.get_id(document), REFERENCE)
            separator = self.get_style('numbering_separator', document)
            number = formatted_number + separator + FixedWidthSpace()
        else:
            number = ''
        text = MixedStyledText(number + self.title, parent=self)
        return ParagraphState(text.spans())

    def render(self, container, last_descender, state=None):
        state = state or self.spans(container.document)
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


class List(GroupedFlowables):
    style_class = ListStyle

    def __init__(self, items, style=None):
        super().__init__(style)
        self.items = items
        # TODO: replace item styles with custom render method

    def flowables(self, document):
        item_style = ListStyle(space_above=0*PT,
                               space_below=self.get_style('item_spacing',
                                                          document))
        last_item_style = ListStyle(space_above=0*PT, space_below=0*PT)
        if self.get_style('ordered', document):
            separator = self.get_style('numbering_separator', document)
            numbers = [format_number(i + 1, self.get_style('numbering_style',
                                                           document))
                       for i in range(len(self.items))]
        else:
            separator = ''
            numbers = [self.get_style('bullet', document)] * len(self.items)
        for i, item in enumerate(self.items[:-1]):
            item = ListItem(numbers[i], separator, item, style=item_style,
                            parent=self)
            yield item
        last = ListItem(numbers[-1], separator, self.items[-1],
                        style=last_item_style, parent=self)
        yield last


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
                                     style=marker_style, parent=self)
        self.flowables = flowables

    def render(self, container, last_descender, state=None):
        if not state:
            try:
                maybe_container = MaybeContainer(container)
                height, _ = self.marker.flow(maybe_container, last_descender)
            except EndOfContainer:
                raise EndOfContainer(state)
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


class Header(ParagraphBase):
    style_class = HeaderStyle

    def spans(self):
        text = Variable(SECTION_NUMBER) + ' ' + Variable(SECTION_TITLE)
        return MixedStyledText(text, parent=self).spans()


class FooterStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Footer(ParagraphBase):
    style_class = FooterStyle

    def spans(self):
        text = Variable(PAGE_NUMBER) + ' / ' + Variable(NUMBER_OF_PAGES)
        return MixedStyledText(text, parent=self).spans()


class TableOfContentsStyle(ParagraphStyle):
    attributes = {'depth': 3}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TableOfContents(GroupedFlowables):
    style_class = TableOfContentsStyle
    location = 'table of contents'

    def __init__(self, style=None, parent=None, styles=[]):
        super().__init__(style=style, parent=parent)
        self.styles = styles
        self.source = self

    def flowables(self, document):
        depth = self.get_style('depth', document)
        for flowable in (flowable for target in document.flowable_targets
                         for flowable in target.flowables):
            if isinstance(flowable, Heading) and flowable.level <= depth:
                flowable_id = flowable.get_id(document)
                text = [Reference(flowable_id, type=REFERENCE), Tab(),
                        Reference(flowable_id, type=TITLE), Tab(),
                        Reference(flowable_id, type=PAGE)]
                for reference in text:
                    reference.source = self
                try:
                    style_index = flowable.level - 1
                    entry = Paragraph(text, style=self.styles[style_index],
                                      parent=self)
                except AttributeError:
                    entry = Paragraph(text, style=self.styles[-1], parent=self)
                yield entry
