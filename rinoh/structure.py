# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from itertools import count, repeat

from .draw import Line, LineStyle
from .flowable import GroupedFlowables, StaticGroupedFlowables
from .flowable import LabeledFlowable, GroupedLabeledFlowables
from .flowable import Flowable, FlowableStyle, GroupedFlowablesStyle
from .number import format_number, NUMBER
from .paragraph import ParagraphStyle, ParagraphBase, Paragraph, ParagraphState
from .reference import Reference, Referenceable, REFERENCE, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, MixedStyledText, FixedWidthSpace, Tab
from .dimension import PT
from .style import PARENT_STYLE


__all__ = ['Section', 'HeadingStyle', 'Heading', 'ListStyle', 'List',
           'ListItem', 'DefinitionListStyle', 'DefinitionList', 'FieldList',
           'HeaderStyle', 'Header', 'FooterStyle', 'Footer',
           'TableOfContentsStyle', 'TableOfContents', 'TableOfContentsEntry',
           'HorizontalRule', 'HorizontalRuleStyle']


class Section(Referenceable, StaticGroupedFlowables):
    def __init__(self, flowables, id=None, style=None, parent=None):
        Referenceable.__init__(self, id)
        StaticGroupedFlowables.__init__(self, flowables, style=style,
                                        parent=parent)

    @property
    def level(self):
        try:
            return self.parent.level + 1
        except AttributeError:
            return 1

    def render(self, container, last_descender, state=None):
        if self.level == 1:
            container.page.section = self
        self.update_page_reference(container.page)
        return super().render(container, last_descender, state=state)


class HeadingStyle(ParagraphStyle):
    attributes = {'numbering_style': NUMBER,
                  'numbering_separator': '.'}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


# TODO: share superclass with List (numbering)
class Heading(ParagraphBase):
    style_class = HeadingStyle

    def __init__(self, title, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.title = title

    def __repr__(self):
        return '{}({}) (style={})'.format(self.__class__.__name__, self.title,
                                          self.style)

    def prepare(self, document):
        element_id = self.parent.get_id(document)
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

    def initial_state(self, document):
        numbering_style = self.get_style('numbering_style', document)
        if numbering_style is not None:
            formatted_number = Reference(self.parent.get_id(document),
                                         REFERENCE)
            separator = self.get_style('numbering_separator', document)
            number = formatted_number + separator + FixedWidthSpace()
        else:
            number = ''
        text = MixedStyledText(number + self.title, parent=self)
        return ParagraphState(text.spans())


class ListStyle(GroupedFlowablesStyle):
    attributes = {'ordered': False,
                  'bullet': SingleStyledText('\N{BULLET}'),
                  'numbering_style': NUMBER,
                  'numbering_separator': ')'}


class List(GroupedLabeledFlowables):
    style_class = ListStyle

    def __init__(self, items, style=None):
        super().__init__(style)
        self.items = items

    def flowables(self, document):
        if self.get_style('ordered', document):
            numbering_style = self.get_style('numbering_style', document)
            numbers = (format_number(i, numbering_style) for i in count(1))
            separator = self.get_style('numbering_separator', document)
        else:
            numbers = repeat(self.get_style('bullet', document))
            separator = ''
        for number, item in zip(numbers, self.items):
            label = Paragraph(number + separator)
            flowable = StaticGroupedFlowables(item)
            yield ListItem(label, flowable, parent=self)


class ListItem(LabeledFlowable):
    pass


class FieldList(GroupedLabeledFlowables, StaticGroupedFlowables):
    pass


class DefinitionListStyle(GroupedFlowablesStyle, ParagraphStyle):
    attributes = {'term_style': PARENT_STYLE,
                  'indentation': 10*PT}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class DefinitionList(GroupedFlowables):
    style_class = DefinitionListStyle

    def __init__(self, items, style=None):
        super().__init__(style)
        self.items = items
        for term, definition in items:
            term.parent = definition.parent = self

    def flowables(self, document):
        term_style = ParagraphStyle(space_above=0*PT,
                                    space_below=0*PT,
                                    base=PARENT_STYLE)
        for i, item in enumerate(self.items):
            term, definition = item
            term_par = Paragraph(term, style=term_style, parent=self)
            yield term_par
            yield definition


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


class TableOfContentsStyle(GroupedFlowablesStyle, ParagraphStyle):
    attributes = {'depth': 3}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TableOfContents(GroupedFlowables):
    style_class = TableOfContentsStyle
    location = 'table of contents'

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.source = self

    def flowables(self, document):
        depth = self.get_style('depth', document)
        for flowable_id, flowable in document.elements.items():
            if isinstance(flowable, Section) and flowable.level <= depth:
                text = [Reference(flowable_id, type=REFERENCE), Tab(),
                        Reference(flowable_id, type=TITLE), Tab(),
                        Reference(flowable_id, type=PAGE)]
                entry = TableOfContentsEntry(text, flowable.level, parent=self)
                yield entry


class TableOfContentsEntry(Paragraph):
    def __init__(self, text_or_items, depth, style=None, parent=None):
        super().__init__(text_or_items, style=style, parent=parent)
        self.depth = depth


class HorizontalRuleStyle(FlowableStyle, LineStyle):
    pass


class HorizontalRule(Flowable):
    style_class = HorizontalRuleStyle

    def render(self, container, descender, state=None):
        width = float(container.width)
        line = Line((0, 0), (width, 0), style=PARENT_STYLE, parent=self)
        line.render(container.canvas)
        return width, 0
