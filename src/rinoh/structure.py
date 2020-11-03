# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from itertools import chain, takewhile

from .attribute import Attribute, Bool, Integer, OverrideDefault
from .draw import Line, LineStyle
from .element import create_destination
from .flowable import GroupedFlowables, StaticGroupedFlowables
from .flowable import LabeledFlowable, GroupedLabeledFlowables
from .flowable import Flowable, FlowableStyle, GroupedFlowablesStyle
from .layout import PageBreakException
from .number import NumberStyle, Label, LabelStyle, format_number
from .number import NumberedParagraph, NumberedParagraphStyle
from .paragraph import ParagraphStyle, ParagraphBase, Paragraph
from .reference import (ReferenceField, ReferencingParagraph,
                        ReferencingParagraphStyle)
from .reference import ReferenceType
from .text import StyledText, SingleStyledText, MixedStyledText, Tab
from .style import PARENT_STYLE
from .strings import StringCollection, String, StringField
from .util import NotImplementedAttribute, itemcount


__all__ = ['Section', 'Heading',
           'ListStyle', 'List', 'ListItem', 'ListItemLabel', 'DefinitionList',
           'Header', 'Footer',
           'TableOfContentsSection', 'TableOfContentsStyle', 'TableOfContents',
           'ListOfStyle',
           'TableOfContentsEntry', 'Admonition', 'AdmonitionStyle',
           'HorizontalRule', 'HorizontalRuleStyle', 'OutOfLineFlowables']


class SectionTitles(StringCollection):
    """Collection of localized titles for common sections"""

    contents = String('Title for the table of contents section')
    list_of_figures = String('Title for the list of figures section')
    list_of_tables = String('Title for the list of tables section')
    chapter = String('Label for top-level sections')
    index = String('Title for the index section')


class SectionStyle(GroupedFlowablesStyle):
    show_in_toc = Attribute(Bool, True, 'List this section in the table of '
                                        'contents')


class NewChapterException(PageBreakException):
    pass


class SectionBase(GroupedFlowables):
    style_class = SectionStyle
    break_exception = NewChapterException

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

    def show_in_toc(self, container):
        parent_show_in_toc = (self.parent is None
                              or self.parent.section is None
                              or self.parent.section.show_in_toc(container))
        return (self.get_style('show_in_toc', container)
                and not self.is_hidden(container)
                and parent_show_in_toc)

    def create_destination(self, container, at_top_of_container=False):
        pass    # destination is set by the section's Heading


class Section(StaticGroupedFlowables, SectionBase):
    """A subdivision of a document

    A section usually has a heading associated with it, which is optionally
    numbered.

    """


class HeadingStyle(NumberedParagraphStyle):
    number_separator = Attribute(StyledText, '.',
                                 "Characters inserted between the number "
                                 "label of the parent section and this "
                                 "section. If ``None``, only show this "
                                 "section's number label.")
    keep_with_next = OverrideDefault(True)


class Heading(NumberedParagraph):
    """The title for a section

    Args:
        title (StyledText): the title text
        custom_label (StyledText): a frontend can supply a custom label to use
            instead of an automatically determined section number

    """

    style_class = HeadingStyle

    def __init__(self, title, custom_label=None,
                 id=None, style=None, parent=None):
        super().__init__(title, id=id, style=style, parent=parent)
        self.custom_label = custom_label

    @property
    def referenceable(self):
        return self.section

    def __repr__(self):
        return '{}({}) (style={})'.format(self.__class__.__name__,
                                          self.content, self.style)

    def prepare(self, flowable_target):
        document = flowable_target.document
        document._sections.append(self.section)
        section_id = self.section.get_id(document)
        numbering_style = self.get_style('number_format', flowable_target)
        if self.get_style('custom_label', flowable_target):
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
            separator = self.get_style('number_separator', flowable_target)
            if separator is not None and self.level > 1:
                parent_id = self.section.parent.section.get_id(document)
                parent_ref = document.get_reference(parent_id, 'number')
                if parent_ref:
                    separator_string = separator.to_string(flowable_target)
                    label = parent_ref + separator_string + label
        else:
            label = None
        title_string = self.content.to_string(flowable_target)
        document.set_reference(section_id, ReferenceType.NUMBER, label)
        document.set_reference(section_id, ReferenceType.TITLE, title_string)

    def text(self, container):
        number = self.number(container)
        return MixedStyledText(number + self.content, parent=self)

    def flow(self, container, last_descender, state=None, **kwargs):
        if self.level == 1 and container.page.chapter_title:
            container.page.create_chapter_title(self)
            result = 0, 0, None
        else:
            result = super().flow(container, last_descender, state, **kwargs)
        return result

    def flow_inner(self, container, descender, state=None, **kwargs):
        result = super().flow_inner(container, descender, state=state, **kwargs)
        create_destination(self.section, container, True)
        return result


class ListStyle(GroupedFlowablesStyle, NumberStyle):
    ordered = Attribute(Bool, False, 'This list is ordered or unordered')
    bullet = Attribute(StyledText, SingleStyledText('\N{BULLET}'),
                       'Bullet to use in unordered lists')


class List(GroupedLabeledFlowables, StaticGroupedFlowables):
    style_class = ListStyle

    def __init__(self, list_items, start_index=1,
                 id=None, style=None, parent=None):
        super().__init__(list_items, id=id, style=style, parent=parent)
        self.start_index = start_index

    def index(self, item, container):
        items = filter(lambda itm: not itm.label.get_style('hide', container),
                       takewhile(lambda li: li != item, self.children))
        return self.start_index + itemcount(items)


class ListItem(LabeledFlowable):
    def __init__(self, flowable, id=None, style=None, parent=None):
        label = ListItemLabel()
        super().__init__(label, flowable, id=id, style=style, parent=parent)


class ListItemLabelStyle(ParagraphStyle, LabelStyle):
    pass


class ListItemLabel(ParagraphBase, Label):
    style_class = ListItemLabelStyle

    def text(self, container):
        list_item = self.parent
        list = list_item.parent
        if list.get_style('ordered', container):
            index = list.index(list_item, container)
            number_format = list.get_style('number_format', container)
            label = format_number(index, number_format)
        else:
            label = list.get_style('bullet', container)
        return MixedStyledText(self.format_label(label, container), parent=self)


class DefinitionList(GroupedLabeledFlowables, StaticGroupedFlowables):
    pass


class Header(Paragraph):
    pass


class Footer(Paragraph):
    pass


class TableOfContentsStyle(GroupedFlowablesStyle, ParagraphStyle):
    depth = Attribute(Integer, 3, 'The number of section levels to include in '
                                  'the table of contents')

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TableOfContentsSection(Section):
    def __init__(self):
        section_title = StringField(SectionTitles, 'contents')
        super().__init__([Heading(section_title, style='unnumbered'),
                          TableOfContents()],
                         style='table of contents')

    def __repr__(self):
        return '{}()'.format(type(self).__name__)

    def get_id(self, document, create=True):
        try:
            return document.metadata['toc_ids'][0]
        except KeyError:
            return super().get_id(document, create)

    def get_ids(self, document):
        yield self.get_id(document)
        yield from document.metadata.get('toc_ids', [])[1:]


class TableOfContents(GroupedFlowables):
    style_class = TableOfContentsStyle
    location = 'table of contents'

    def __init__(self, local=False, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.local = local
        self.source = self

    def __repr__(self):
        args = ''.join(', {}={}'.format(name, repr(getattr(self, name)))
                       for name in ('id', 'style')
                       if getattr(self, name) is not None)
        return '{}(local={}{})'.format(type(self).__name__, self.local, args)

    def flowables(self, container):
        def limit_items(items, section):
            while next(items) is not section:  # fast-forward `items` to the
                pass                           # first sub-section of `section`
            for item in items:
                if item.level <= section.level:
                    break
                yield item

        depth = self.get_style('depth', container)
        if self.local and self.section:
            depth += self.level - 1
        items = (section for section in container.document._sections
                 if section.show_in_toc(container) and section.level <= depth)
        if self.local and self.section:
            items = limit_items(items, self.section)
        for section in items:
            yield TableOfContentsEntry(section, parent=self)


class TableOfContentsEntryStyle(ReferencingParagraphStyle):
    text = OverrideDefault(ReferenceField('number')
                           + Tab() + ReferenceField('title')
                           + Tab() + ReferenceField('page'))


class TableOfContentsEntry(ReferencingParagraph):
    style_class = TableOfContentsEntryStyle

    def __init__(self, flowable, id=None, style=None, parent=None):
        super().__init__(flowable, id=id, style=style, parent=parent)

    @property
    def depth(self):
        return self.target_id_or_flowable.level


class ListOfSection(Section):
    list_class = NotImplementedAttribute()

    def __init__(self):
        key = 'list_of_{}s'.format(self.list_class.category.lower())
        section_title = StringField(SectionTitles, key)
        self.list_of = self.list_class()
        super().__init__([Heading(section_title, style='unnumbered'),
                          self.list_of],
                         style='list of {}'.format(self.category))

    def __repr__(self):
        return '{}()'.format(type(self).__name__)

    def is_hidden(self, container):
        return (super().is_hidden(container)
                or self.list_of.is_hidden(container))


class ListOfStyle(GroupedFlowablesStyle, ParagraphStyle):
    pass


class ListOf(GroupedFlowables):
    category = NotImplementedAttribute()
    style_class = ListOfStyle

    def __init__(self, local=False, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.local = local
        self.source = self

    def __repr__(self):
        args = ''.join(', {}={}'.format(name, repr(getattr(self, name)))
                       for name in ('id', 'style')
                       if getattr(self, name) is not None)
        return '{}(local={}{})'.format(type(self).__name__, self.local, args)

    @property
    def location(self):
        return 'List of {}s'.format(self.category)

    def is_hidden(self, container):
        try:
            next(self.flowables(container))
        except StopIteration:
            return True
        return False

    def flowables(self, container):
        document = container.document
        category_counters = document.counters.get(self.category, {})

        def limit_items(items, section):
            for item in items:                # fast-forward `items` to the
                if item.section is section:   # first sub-section of `section`
                    yield item
                    break
            for item in items:
                if not (item.section.level > section.level
                        or item.section is section):
                    break
                yield item

        def items_in_section(section):
            section_id = (section.get_id(document, create=False)
                          if section else None)
            yield from category_counters.get(section_id, [])

        items = chain(items_in_section(None),
                      *(items_in_section(section)
                        for section in document._sections))

        if self.local and self.section:
            items = limit_items(items, self.section)
        for caption in items:
            yield ListOfEntry(caption.referenceable, parent=self)


class ListOfEntryStyle(ReferencingParagraphStyle):
    text = OverrideDefault(ReferenceField('reference')
                           + ': ' + ReferenceField('title')
                           + Tab() + ReferenceField('page'))


class ListOfEntry(ReferencingParagraph):
    style_class = ListOfEntryStyle


class AdmonitionStyle(GroupedFlowablesStyle):
    inline_title = Attribute(Bool, True, "Show the admonition's title inline "
                                         "with the body text, if possible")


class AdmonitionTitles(StringCollection):
    """Collection of localized titles for common admonitions"""

    attention = String('Title for attention admonitions')
    caution = String('Title for caution admonitions')
    danger = String('Title for danger admonitions')
    error = String('Title for error admonitions')
    hint = String('Title for hint admonitions')
    important = String('Title for important admonitions')
    note = String('Title for note admonitions')
    tip = String('Title for tip admonitions')
    warning = String('Title for warning admonitions')
    seealso = String('Title for see-also admonitions')


class Admonition(StaticGroupedFlowables):
    style_class = AdmonitionStyle

    def __init__(self, flowables, title=None, type=None,
                 id=None, style=None, parent=None):
        super().__init__(flowables, id=id, style=style, parent=parent)
        self.custom_title = title
        self.admonition_type = type

    def title(self, document):
        return (self.custom_title
                or document.get_string(AdmonitionTitles,
                                       self.admonition_type))

    def flowables(self, container):
        title = self.title(container.document)
        flowables = super().flowables(container)
        first_flowable = next(flowables)
        inline_title = self.get_style('inline_title', container)
        if inline_title and isinstance(first_flowable, Paragraph):
            title = MixedStyledText(title, style='inline title')
            kwargs = dict(id=first_flowable.id, style=first_flowable.style,
                          parent=self)
            paragraph = Paragraph(title + ' ' + first_flowable, **kwargs)
            paragraph.secondary_ids = first_flowable.secondary_ids
            yield paragraph
        else:
            yield Paragraph(title, style='title', parent=self)
            yield first_flowable
        for flowable in flowables:
            yield flowable


class HorizontalRuleStyle(FlowableStyle, LineStyle):
    pass


class HorizontalRule(Flowable):
    style_class = HorizontalRuleStyle

    def render(self, container, descender, state, **kwargs):
        width = float(container.width)
        line = Line((0, 0), (width, 0), style=PARENT_STYLE, parent=self)
        line.render(container)
        return width, 0, 0


class OutOfLineFlowables(GroupedFlowables):
    def __init__(self, name, align=None, width=None, id=None, style=None,
                 parent=None):
        super().__init__(align=align, width=width, id=id, style=style,
                         parent=parent)
        self.name = name

    def flowables(self, container):
        return container.document.supporting_matter[self.name]
