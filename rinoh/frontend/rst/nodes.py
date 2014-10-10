
import re
import unicodedata

import rinoh as rt

from . import (CustomElement, BodyElement, BodySubElement, InlineElement,
               GroupingElement)
from ...util import intersperse


class Text(InlineElement):
    RE_NORMALIZE_SPACE = re.compile('[\t\r\n ]+')

    def styled_text(self, preserve_space=False):
        if preserve_space:
            return self.node
        else:
            return self.RE_NORMALIZE_SPACE.sub(' ', self.node)


class Document(BodyElement):
    pass


class DocInfo(BodyElement):
    def build_flowable(self):
        return rt.FieldList([child.flowable() for child in self.getchildren()])


# bibliographic elements

class DocInfoField(BodyElement):
    def build_flowable(self, content=None):
        field_name = rt.Paragraph(self.__class__.__name__, style='field_name')
        content = content or rt.Paragraph(self.process_content())
        return rt.LabeledFlowable(field_name, content)


class Author(DocInfoField):
    pass


class Authors(DocInfoField):
    def build_flowable(self):
        authors = []
        for author in self.author:
            authors.append(rt.Paragraph(author.process_content()))
        return super().build_flowable(rt.StaticGroupedFlowables(authors))


class Copyright(DocInfoField):
    pass


class Address(DocInfoField):
    pass


class Organization(DocInfoField):
    pass


class Contact(DocInfoField):
    pass


class Date(DocInfoField):
    pass


class Version(DocInfoField):
    pass


class Revision(DocInfoField):
    pass


class Status(DocInfoField):
    pass


# FIXME: the meta elements are removed from the docutils doctree
class Meta(BodyElement):
    MAP = {'keywords': 'keywords',
           'description': 'subject'}

    def build_flowable(self):
        metadata = {self.MAP[self.get('name')]: self.get('content')}
        return rt.SetMetadataFlowable(**metadata)


# body elements

class System_Message(BodyElement):
    def build_flowable(self):
        return rt.WarnFlowable(self.text)


class Comment(BodyElement):
    def build_flowable(self):
        return rt.DummyFlowable()


class Topic(GroupingElement):
    style = 'topic'

    def build_flowable(self):
        classes = self.get('classes')
        if 'contents' in classes:
            flowables = [rt.TableOfContents(local='local' in classes)]
            try:
                flowables.insert(0, self.title.flowable())
            except AttributeError:
                pass
            return rt.StaticGroupedFlowables(flowables,
                                             style='table of contents')
        else:
            return super().build_flowable()


class Rubric(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(self.process_content(), style='rubric')


class Sidebar(GroupingElement):
    def flowable(self):
        grouped_flowables = super().flowable()
        return rt.Framed(grouped_flowables, style='sidebar')


class Section(BodyElement):
    def build_flowable(self):
        flowables = []
        for element in self.getchildren():
            flowables.append(element.flowable())
        return rt.Section(flowables)


class Paragraph(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(super().process_content())


class Compound(GroupingElement):
    pass


class Title(BodyElement):
    def build_flowable(self):
        if isinstance(self.parent, Section):
            try:
                kwargs = dict(custom_label=self.generated.build_styled_text())
            except AttributeError:
                kwargs = dict()
            return rt.Heading(self.process_content(), **kwargs)
        else:
            return rt.Paragraph(self.process_content(), style='title')


class Subtitle(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(self.text, style='subtitle')


class Admonition(GroupingElement):
    def flowable(self):
        return rt.Framed(super().flowable(), style='admonition')


class AdmonitionBase(GroupingElement):
    title = None

    def flowable(self):
        title_par = rt.Paragraph(self.title, style='title')
        content = rt.StaticGroupedFlowables([title_par, super().flowable()])
        framed = rt.Framed(content, style='admonition')
        framed.admonition_type = self.__class__.__name__.lower()
        return framed


class Attention(AdmonitionBase):
    title = 'Attention!'


class Caution(AdmonitionBase):
    title = 'Caution!'


class Danger(AdmonitionBase):
    title = '!DANGER!'


class Error(AdmonitionBase):
    title = 'Error'


class Hint(AdmonitionBase):
    title = 'Hint'


class Important(AdmonitionBase):
    title = 'Important'


class Note(AdmonitionBase):
    title = 'Note'


class Tip(AdmonitionBase):
    title = 'Tip'


class Warning(AdmonitionBase):
    title = 'Warning'


class Generated(InlineElement):
    def styled_text(self, preserve_space=False):
        return None

    def build_styled_text(self):
        return self.process_content()


class Emphasis(InlineElement):
    def build_styled_text(self):
        return rt.Emphasized(self.text)


class Strong(InlineElement):
    def build_styled_text(self):
        return rt.Bold(self.text)


class Title_Reference(InlineElement):
    def build_styled_text(self):
        return rt.Italic(self.text)


class Literal(InlineElement):
    def build_styled_text(self):
        text = self.text.replace('\n', ' ')
        return rt.SingleStyledText(text, style='monospaced')


class Superscript(InlineElement):
    def build_styled_text(self):
        return rt.Superscript(self.process_content())


class Subscript(InlineElement):
    def build_styled_text(self):
        return rt.Subscript(self.process_content())


class Problematic(BodyElement, InlineElement):
    def build_styled_text(self):
        return rt.SingleStyledText(self.text, style='error')

    def build_flowable(self):
        return rt.DummyFlowable()


class Literal_Block(BodyElement):
    def build_flowable(self):
        text = self.text.replace(' ', unicodedata.lookup('NO-BREAK SPACE'))
        return rt.Paragraph(text, style='literal')


class Block_Quote(GroupingElement):
    style = 'block quote'


class Attribution(Paragraph):
    def build_flowable(self):
        return rt.Paragraph('\N{EM DASH}' + self.process_content(),
                            style='attribution')


class Line_Block(GroupingElement):
    style = 'line block'


class Line(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(self.process_content() or '\n',
                            style='line block line')


class Doctest_Block(BodyElement):
    def build_flowable(self):
        text = self.text.replace(' ', unicodedata.lookup('NO-BREAK SPACE'))
        return rt.Paragraph(text, style='literal')


class Reference(BodyElement, InlineElement):
    def build_styled_text(self):
        if 'refid' in self.attributes:
            link = rt.NamedDestinationLink(self.get('refid'))
        elif 'refuri' in self.attributes:
            link = rt.HyperLink(self.get('refuri'))
        return rt.AnnotatedText(self.process_content(), link, style='link')

    def build_flowable(self):
        children = self.getchildren()
        assert len(children) == 1
        return self.image.flowable()


class Footnote(BodyElement):
    def flowable(self):
        return rt.RegisterNote(super().flowable())

    def build_flowable(self):
        content = [node.flowable() for node in self.getchildren()[1:]]
        return rt.Note(rt.StaticGroupedFlowables(content))


class Label(BodyElement):
    def build_flowable(self):
        return rt.DummyFlowable()


class Footnote_Reference(InlineElement):
    style = 'footnote'

    def build_styled_text(self):
        return rt.NoteMarkerByID(self.node['refid'],
                                 custom_label=self.process_content(),
                                 style=self.style)


class Citation(Footnote):
    pass


class Citation_Reference(Footnote_Reference):
    style = 'citation'


class Substitution_Definition(BodyElement):
    def build_flowable(self):
        return rt.DummyFlowable()


class Target(BodyElement, InlineElement):
    def build_styled_text(self):
        destination = rt.NamedDestination(self.get('ids')[0])
        return rt.AnnotatedText(self.process_content(), destination)

    def build_flowable(self):
        return rt.DummyFlowable()


class Enumerated_List(BodyElement):
    def build_flowable(self):
        # TODO: handle different numbering styles
        return rt.List([item.process() for item in self.list_item],
                       style='enumerated')


class Bullet_List(BodyElement):
    def build_flowable(self):
        return rt.List([item.process() for item in self.list_item],
                       style='bulleted')


class List_Item(BodySubElement):
    def process(self):
        return [item.flowable() for item in self.getchildren()]


class Definition_List(BodyElement):
    def build_flowable(self):
        return rt.DefinitionList([item.process()
                                  for item in self.definition_list_item])


class Definition_List_Item(BodySubElement):
    def process(self):
        term = self.term.styled_text()
        try:
            term += ' : ' + self.classifier.styled_text()
        except AttributeError:
            pass
        return term, self.definition.flowable()


class Term(InlineElement):
    def build_styled_text(self):
        return self.process_content()


class Classifier(InlineElement):
    def build_styled_text(self):
        return self.process_content('classifier')


class Definition(GroupingElement):
    pass


class Field_List(BodyElement):
    def build_flowable(self):
        return rt.FieldList([field.flowable() for field in self.field])


class Field(BodyElement):
    def build_flowable(self):
        return rt.LabeledFlowable(self.field_name.flowable(),
                                  self.field_body.flowable())


class Field_Name(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(self.process_content(), style='field_name')


class Field_Body(GroupingElement):
    pass


class Option_List(BodyElement):
    def build_flowable(self):
        return rt.FieldList([item.flowable() for item in self.option_list_item])


class Option_List_Item(BodyElement):
    def build_flowable(self):
        return rt.LabeledFlowable(self.option_group.flowable(),
                                  self.description.flowable(), style='option')


class Option_Group(BodyElement):
    def build_flowable(self):
        options = (option.styled_text() for option in self.option)
        return rt.Paragraph(intersperse(options, ', '), style='option_group')


class Option(InlineElement):
    def build_styled_text(self):
        text = self.option_string.styled_text()
        try:
            delimiter = rt.MixedStyledText(self.option_argument['delimiter'],
                                           style='option_string')
            text += delimiter + self.option_argument.styled_text()
        except AttributeError:
            pass
        return rt.MixedStyledText(text)


class Option_String(InlineElement):
    def build_styled_text(self):
        return rt.MixedStyledText(self.process_content(), style='option_string')


class Option_Argument(InlineElement):
    def build_styled_text(self):
        return rt.MixedStyledText(self.process_content(), style='option_arg')


class Description(GroupingElement):
    pass


class Image(BodyElement, InlineElement):
    @property
    def image_path(self):
        return self.get('uri').rsplit('.png', 1)[0]

    def build_flowable(self):
        return rt.Image(self.image_path)

    def build_styled_text(self):
        return rt.InlineImage(self.image_path)


class Figure(GroupingElement):
    grouped_flowables_class = rt.Figure


class Caption(BodyElement):
    def build_flowable(self):
        return rt.Caption(super().process_content())


class Legend(GroupingElement):
    style = 'legend'


class Transition(BodyElement):
    def build_flowable(self):
        return rt.HorizontalRule()


class Table(BodyElement):
    def build_flowable(self):
        data = ReStructuredTextTabularData(self)
        return rt.Tabular(data)


class TGroup(CustomElement):
    pass


class TableRowGroup(CustomElement):
    def get_rows(self):
        rows = []
        spanned_cells = []
        for r, row in enumerate(self.row):
            row_cells = []
            cells = row.getchildren()
            index = c = 0
            while index < len(cells):
                if (r, c) in spanned_cells:
                    cell = None
                else:
                    rowspan = int(cells[index].get('rowspan', 1))
                    colspan = int(cells[index].get('colspan', 1))
                    cell = rt.TabularCell(cells[index].text, rowspan, colspan)
                    if rowspan > 1 or colspan > 1:
                        for j in range(c, c + colspan):
                            for i in range(r, r + rowspan):
                                spanned_cells.append((i, j))
                    index += 1
                row_cells.append(cell)
                c += 1
            rows.append(rt.TabularRow(row_cells))
        return rt.Array(rows)


class THead(TableRowGroup):
    pass


class TBody(TableRowGroup):
    pass


class Row(CustomElement):
    pass


class Entry(GroupingElement):
    def get_cell(self):
        rowspan = self.get('morerows', 1)
        colspan = self.get('morecols', 1)
        return rt.TabularCell(self.flowable(), rowspan, colspan)


class ReStructuredTextTabularData(rt.TabularData):
    def __init__(self, node):
        tgroup = node.tgroup
        try:
            head = tgroup.thead.get_rows()
        except AttributeError:
            head = None
        body = tgroup.tbody.get_rows()
        # column_groups, column_options = self.parse_column_options(node)
        column_groups, column_options = None, None
        super().__init__(body, head, None, column_options, column_groups)

    # def parse_column_options(self, element):
    #     try:
    #         column_groups = []
    #         column_options = []
    #         for colgroup in element.colgroup:
    #             span = int(colgroup.get('span', 1))
    #             width = colgroup.get('width')
    #             column_groups.append(span)
    #             options = [{'width': width} for c in range(span)]
    #             try:
    #                 for c, col in enumerate(colgroup.col):
    #                     if 'width' in col.attrib:
    #                         options[c]['width'] = col.get('width')
    #             except AttributeError:
    #                 pass
    #             column_options += options
    #         return column_groups, column_options
    #     except AttributeError:
    #         return None, None
