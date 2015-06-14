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
from .flowable import PageBreak, PageBreakState
from .layout import EndOfContainer
from .number import NumberStyle, Label, format_number
from .number import NumberedParagraph, NumberedParagraphStyle
from .paragraph import ParagraphStyle, Paragraph
from .reference import Referenceable, Reference
from .reference import NUMBER, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, MixedStyledText, Tab
from .style import PARENT_STYLE


__all__ = ['Section', 'Heading', 'ListStyle', 'List', 'ListItem', 'FieldList',
           'DefinitionList', 'DefinitionTerm',
           'HeaderStyle', 'Header', 'FooterStyle', 'Footer',
           'TableOfContentsStyle', 'TableOfContents', 'TableOfContentsEntry',
           'HorizontalRule', 'HorizontalRuleStyle']


class SectionSytyle(GroupedFlowablesStyle):
    attributes = {'show_in_toc': True,
                  'new_page': False}    # False, True, LEFT, RIGHT


class Section(Referenceable, StaticGroupedFlowables):
    style_class = SectionSytyle

    def __init__(self, flowables, id=None, style=None, parent=None):
        super().__init__(flowables, id=id, style=style, parent=parent)

    @property
    def level(self):
        try:
            return self.parent.level + 1
        except AttributeError:
            return 1

    @property
    def section(self):
        return self

    def flowables(self, document):
        new_page = self.get_style('new_page', document)
        if new_page:
            yield PageBreak(new_page)
        for flowable in super().flowables(document):
            yield flowable

    def show_in_toc(self, document):
        show_in_toc = self.get_style('show_in_toc', document)
        try:
            parent_show_in_toc = self.parent.show_in_toc(document)
        except AttributeError:
            parent_show_in_toc = True
        return show_in_toc and parent_show_in_toc

    def render(self, container, descender, state=None, **kwargs):
        set_section = True
        try:
            return super().render(container, descender, state=state, **kwargs)
        except EndOfContainer as eoc:
            first_flowable_state = eoc.flowable_state.first_flowable_state
            set_section = not isinstance(first_flowable_state, PageBreakState)
            raise eoc
        finally:
            if set_section:
                container.page.set_current_section(self.section, state is None)



class HeadingStyle(NumberedParagraphStyle):
    attributes = {'number_separator': '.'}


class Heading(NumberedParagraph):
    style_class = HeadingStyle

    def __init__(self, title, custom_label=None,
                 id=None, style=None, parent=None):
        super().__init__(title, id=id, style=style, parent=parent)
        self.custom_label = custom_label

    @property
    def referenceable(self):
        return self.section

    def __repr__(self):
        return '{}({}) (style={})'.format(self.__class__.__name__, self.content,
                                          self.style)

    def prepare(self, document):
        section_id = self.section.get_id(document)
        numbering_style = self.get_style('number_format', document)
        if self.get_style('custom_label', document):
            assert self.custom_label is not None
            label = str(self.custom_label)
        elif numbering_style:
            try:
                parent_section_id = self.section.parent.section.get_id(document)
            except AttributeError:
                parent_section_id = None
            heading_counters = document.counters.setdefault(__class__, {})
            section_counter = heading_counters.setdefault(parent_section_id, [])
            section_counter.append(self)
            number = len(section_counter)
            label = format_number(number, numbering_style)
            separator = self.get_style('number_separator', document)
            if separator is not None and self.level > 1:
                parent_id = self.section.parent.section.get_id(document)
                parent_ref = document.get_reference(parent_id, NUMBER)
                label = parent_ref + separator + label
        else:
            label = None
        document.set_reference(section_id, NUMBER, label)
        document.set_reference(section_id, TITLE, str(self.content))

    def text(self, document):
        number = self.number(document)
        return MixedStyledText(number + self.content, parent=self)

    def render(self, container, last_descender, state=None):
        result = super().render(container, last_descender, state=state)
        try:
            self.parent.update_page_reference(container.page)
        except AttributeError:
            pass    # parent is not a Referenceable
        return result


class ListStyle(GroupedFlowablesStyle, NumberStyle):
    attributes = {'ordered': False,
                  'bullet': SingleStyledText('\N{BULLET}')}


class List(GroupedLabeledFlowables, Label):
    style_class = ListStyle

    def __init__(self, items, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.items = items

    def flowables(self, document):
        if self.get_style('ordered', document):
            number_format = self.get_style('number_format', document)
            numbers = (format_number(i, number_format) for i in count(1))
        else:
            numbers = repeat(self.get_style('bullet', document))
        for number, item in zip(numbers, self.items):
            label = Paragraph(self.format_label(number, document))
            flowable = StaticGroupedFlowables(item)
            yield ListItem(label, flowable, parent=self)


class ListItem(LabeledFlowable):
    pass


class FieldList(GroupedLabeledFlowables, StaticGroupedFlowables):
    pass


class DefinitionList(GroupedFlowables):
    def __init__(self, items, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.items = items
        for term, definition in items:
            term.parent = self
            definition.parent = self

    def flowables(self, document):
        for (term, definition) in self.items:
            yield term
            yield definition


class DefinitionTerm(Paragraph):
    pass


class HeaderStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Header(Paragraph):
    style_class = HeaderStyle

    def __init__(self, text=None, id=None, style=None, parent=None):
        text = text or Variable(SECTION_NUMBER) + ' ' + Variable(SECTION_TITLE)
        super().__init__(text, id=id, style=style, parent=parent)


class FooterStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Footer(Paragraph):
    style_class = FooterStyle

    def __init__(self, text=None, id=None, style=None, parent=None):
        text = text or (Tab() + Variable(PAGE_NUMBER) + ' / '
                        + Variable(NUMBER_OF_PAGES))
        super().__init__(text, id=id, style=style, parent=parent)


class TableOfContentsStyle(GroupedFlowablesStyle, ParagraphStyle):
    attributes = {'depth': 3}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TableOfContents(GroupedFlowables):
    style_class = TableOfContentsStyle
    location = 'table of contents'

    def __init__(self, local=False, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.local = local
        self.source = self

    def flowables(self, document):
        def limit_items(items, section):
            section_id = section.get_id(document)
            section_level = section.level

            # fast-forward `items` to the first sub-section of `section`
            while next(items)[0] != section_id:
                pass

            for flowable_id, flowable in items:
                if flowable.level == section_level:
                    break
                yield flowable_id, flowable

        depth = self.get_style('depth', document)
        items = ((flowable_id, flowable)
                 for flowable_id, flowable in document.elements.items()
                 if (isinstance(flowable, Section)
                     and flowable.show_in_toc(document)
                     and flowable.level <= depth))
        if self.local and self.section:
            items = limit_items(items, self.section)

        for flowable_id, flowable in items:
            text = [Reference(flowable_id, type=NUMBER, quiet=True), Tab(),
                    Reference(flowable_id, type=TITLE), Tab(),
                    Reference(flowable_id, type=PAGE)]
            yield TableOfContentsEntry(text, flowable.level, parent=self)


class TableOfContentsEntry(Paragraph):
    def __init__(self, text_or_items, depth, id=None, style=None, parent=None):
        super().__init__(text_or_items, id=id, style=style, parent=parent)
        self.depth = depth


class HorizontalRuleStyle(FlowableStyle, LineStyle):
    pass


class HorizontalRule(Flowable):
    style_class = HorizontalRuleStyle

    def render(self, container, descender, state=None):
        width = float(container.width)
        line = Line((0, 0), (width, 0), style=PARENT_STYLE, parent=self)
        line.render(container)
        return width, 0
