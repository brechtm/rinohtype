# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .draw import Line, LineStyle
from .flowable import GroupedFlowables, StaticGroupedFlowables
from .flowable import PageBreak, PageBreakStyle
from .flowable import LabeledFlowable, GroupedLabeledFlowables
from .flowable import Flowable, FlowableStyle, GroupedFlowablesStyle
from .number import NumberStyle, Label, LabelStyle, format_number
from .number import NumberedParagraph, NumberedParagraphStyle
from .paragraph import ParagraphStyle, ParagraphBase, Paragraph
from .reference import Referenceable, Reference
from .reference import NUMBER, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, MixedStyledText, Tab
from .style import PARENT_STYLE


__all__ = ['Section', 'Heading',
           'ListStyle', 'List', 'ListItem', 'ListItemLabel',
           'FieldList', 'DefinitionList', 'DefinitionTerm', 'Definition',
           'HeaderStyle', 'Header', 'FooterStyle', 'Footer',
           'TableOfContentsStyle', 'TableOfContents', 'TableOfContentsEntry',
           'HorizontalRule', 'HorizontalRuleStyle']


class SectionStyle(GroupedFlowablesStyle, PageBreakStyle):
    attributes = {'show_in_toc': True}


class Section(Referenceable, StaticGroupedFlowables, PageBreak):
    category = 'Section'
    style_class = SectionStyle

    def __init__(self, flowables, id=None, style=None, parent=None):
        super().__init__(flowables, id=id, style=style, parent=parent)

    @property
    def category(self):
        return 'Chapter' if self.level == 1 else 'Section'

    @property
    def level(self):
        try:
            return self.parent.level + 1
        except AttributeError:
            return 1

    @property
    def section(self):
        return self

    def show_in_toc(self, document):
        show_in_toc = self.get_style('show_in_toc', document)
        try:
            parent_show_in_toc = self.parent.show_in_toc(document)
        except AttributeError:
            parent_show_in_toc = True
        return show_in_toc and parent_show_in_toc


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

    def prepare(self, flowable_target):
        document = flowable_target.document
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
            ref_category = self.referenceable.category
            section_counters = document.counters.setdefault(ref_category, {})
            section_counter = section_counters.setdefault(parent_section_id, [])
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


class List(StaticGroupedFlowables, Label):
    style_class = ListStyle

    def __init__(self, flowables, id=None, style=None, parent=None):
        items = [ListItem(i + 1, flowable, parent=self)
                 for i, flowable in enumerate(flowables)]
        super().__init__(items, id=id, style=style, parent=parent)


class ListItem(LabeledFlowable):
    def __init__(self, index, flowable, id=None, style=None, parent=None):
        label = ListItemLabel(index)
        super().__init__(label, flowable, id=id, style=style, parent=parent)


class ListItemLabelStyle(ParagraphStyle, LabelStyle):
    pass


class ListItemLabel(ParagraphBase, Label):
    style_class = ListItemLabelStyle

    def __init__(self, index, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.index = index

    def text(self, document):
        list = self.parent.parent
        if list.get_style('ordered', document):
            number_format = list.get_style('number_format', document)
            label = format_number(self.index, number_format)
        else:
            label = list.get_style('bullet', document)
        return MixedStyledText(self.format_label(label, document), parent=self)


class FieldList(GroupedLabeledFlowables, StaticGroupedFlowables):
    pass


class DefinitionList(StaticGroupedFlowables):
    def __init__(self, term_and_definition_pairs, id=None, style=None,
                 parent=None):
        flowables = [item for term, definition in term_and_definition_pairs
                     for item in (term, definition)]
        super().__init__(flowables, id=id, style=style, parent=parent)


class DefinitionTerm(StaticGroupedFlowables):
    pass


class Definition(StaticGroupedFlowables):
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
            yield TableOfContentsEntry(flowable, parent=self)


class TableOfContentsEntryStyle(ParagraphStyle):
    attributes = {'show_number': True}


class TableOfContentsEntry(ParagraphBase):
    style_class = TableOfContentsEntryStyle

    def __init__(self, flowable, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.flowable = flowable

    @property
    def depth(self):
        return  self.flowable.level

    def text(self, document):
        flowable_id = self.flowable.get_id(document)
        text = [Reference(flowable_id, type=TITLE), Tab(),
                Reference(flowable_id, type=PAGE)]
        if self.get_style('show_number', document):
            number_ref = Reference(flowable_id, type=NUMBER, quiet=True)
            text = [number_ref, Tab()] + text
        return MixedStyledText(text, parent=self)


class HorizontalRuleStyle(FlowableStyle, LineStyle):
    pass


class HorizontalRule(Flowable):
    style_class = HorizontalRuleStyle

    def render(self, container, descender, state=None):
        width = float(container.width)
        line = Line((0, 0), (width, 0), style=PARENT_STYLE, parent=self)
        line.render(container)
        return width, 0
