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
from .number import NumberedParagraph, NumberStyle, format_number
from .paragraph import ParagraphStyle, Paragraph
from .reference import Referenceable, Reference
from .reference import REFERENCE, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, MixedStyledText, Tab
from .dimension import PT
from .style import PARENT_STYLE


__all__ = ['Section', 'Heading', 'ListStyle', 'List', 'ListItem',
           'DefinitionListStyle', 'DefinitionList', 'FieldList',
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


class Heading(NumberedParagraph):
    def __init__(self, title, style=None, parent=None):
        super().__init__(title, style=style, parent=parent)

    def __repr__(self):
        return '{}({}) (style={})'.format(self.__class__.__name__, self.title,
                                          self.style)

    def prepare(self, document):
        section_id = self.parent.get_id(document)
        numbering_style = self.get_style('number_format', document)
        if numbering_style:
            heading_counters = document.counters.setdefault(__class__, {})
            level_counter = heading_counters.setdefault(self.level, [])
            level_counter.append(self)
            number = len(level_counter)
            formatted_number = format_number(number, numbering_style)
        else:
            formatted_number = None
        document.set_reference(section_id, REFERENCE, formatted_number)
        document.set_reference(section_id, TITLE, str(self.content))

    def text(self, document):
        number = self.number(document)
        return MixedStyledText(number + self.content, parent=self)

    def render(self, container, last_descender, state=None):
        result = super().render(container, last_descender, state=state)
        if self.level == 1:
            container.page.section = self.parent
        self.parent.update_page_reference(container.page)
        return result


class ListStyle(GroupedFlowablesStyle, NumberStyle):
    attributes = {'ordered': False,
                  'bullet': SingleStyledText('\N{BULLET}')}


class List(GroupedLabeledFlowables):
    style_class = ListStyle

    def __init__(self, items, style=None):
        super().__init__(style)
        self.items = items

    def flowables(self, document):
        if self.get_style('ordered', document):
            number_format = self.get_style('number_format', document)
            numbers = (format_number(i, number_format) for i in count(1))
            separator = self.get_style('number_separator', document)
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


class Header(Paragraph):
    style_class = HeaderStyle

    def __init__(self, style=None, parent=None):
        text = Variable(SECTION_NUMBER) + ' ' + Variable(SECTION_TITLE)
        super().__init__(text, style=style, parent=parent)


class FooterStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Footer(Paragraph):
    style_class = FooterStyle

    def __init__(self, style=None, parent=None):
        text = Variable(PAGE_NUMBER) + ' / ' + Variable(NUMBER_OF_PAGES)
        super().__init__(text, style=style, parent=parent)


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
