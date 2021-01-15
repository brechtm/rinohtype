# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from datetime import datetime

import rinoh as rt

from . import (DocutilsInlineNode, DocutilsNode, DocutilsBodyNode,
               DocutilsGroupingNode, DocutilsDummyNode)
from ...dimension import DimensionUnit, INCH, CM, MM, PT, PICA, PERCENT
from ...util import intersperse


# Support for the following nodes is still missing
# (http://docutils.sourceforge.net/docs/ref/doctree.html)
# - abbreviation? (not exposed in default reStructuredText; Sphinx has :abbr:)
# - acronym (not exposed in default reStructuredText?)
# - pending (should not appear in final doctree?)
# - substitution_reference (should not appear in final doctree?)


class Text(DocutilsInlineNode):
    node_name = '#text'

    def styled_text(self):
        return self.text


class Inline(DocutilsInlineNode):
    style = None
    class_styles = {}

    @property
    def style_from_class(self):
        for cls in self.get('classes'):
            if cls in self.class_styles:
                return self.class_styles[cls]
        return self.style

    def build_styled_text(self):
        return self.process_content(style=self.style_from_class)


class Document(DocutilsBodyNode):
    pass


class DocInfo(DocutilsBodyNode):
    def build_flowable(self):
        doc_info = {field.name: field.value for field in self.getchildren()}
        return rt.SetMetadataFlowable(**doc_info)


class Decoration(DocutilsGroupingNode):
    pass


class Header(DocutilsBodyNode):
    def build_flowable(self):
        return rt.WarnFlowable('Docutils header nodes are ignored. Please '
                               'configure your document template instead.')


class Footer(DocutilsBodyNode):
    def build_flowable(self):
        return rt.WarnFlowable('Docutils footer nodes are ignored. Please '
                               'configure your document template instead.')


# bibliographic elements

class DocInfoField(DocutilsInlineNode):
    @property
    def name(self):
        return self.tag_name

    @property
    def value(self):
        return self.styled_text()


class Author(DocInfoField):
    pass


class Authors(DocInfoField):
    @property
    def value(self):
        return [author.styled_text() for author in self.author]


class Copyright(DocInfoField):
    pass


class Address(DocInfoField):
    pass


class Organization(DocInfoField):
    pass


class Contact(DocInfoField):
    pass


class Date(DocInfoField):
    @property
    def value(self):
        try:
            return datetime.strptime(self.node.astext(), '%Y-%m-%d')
        except ValueError:
            return super().value


class Version(DocInfoField):
    pass


class Revision(DocInfoField):
    pass


class Status(DocInfoField):
    pass


# FIXME: the meta elements are removed from the docutils doctree
class Meta(DocutilsBodyNode):
    MAP = {'keywords': 'keywords',
           'description': 'subject'}

    def build_flowable(self):
        metadata = {self.MAP[self.get('name')]: self.get('content')}
        return rt.SetMetadataFlowable(**metadata)


# body elements

class System_Message(DocutilsBodyNode):
    def build_flowable(self):
        return rt.WarnFlowable(self.text)


class Comment(DocutilsDummyNode):
    pass


class Topic(DocutilsGroupingNode):
    style = 'topic'

    def _process_topic(self, topic_type):
        topic = super().build_flowable(style=topic_type)
        del topic.children[0]
        return rt.SetMetadataFlowable(**{topic_type: topic})

    @property
    def set_id(self):
        classes = self.get('classes')
        return not ('contents' in classes and 'local' not in classes)

    def build_flowable(self):
        classes = self.get('classes')
        if 'contents' in classes:
            if 'local' in classes:
                flowables = [rt.TableOfContents(local=True)]
                try:
                    flowables.insert(0, self.title.flowable())
                except AttributeError:
                    pass
                return rt.StaticGroupedFlowables(flowables,
                                                 style='table of contents')
            else:
                return rt.SetMetadataFlowable(toc_ids=self.get('ids'))
        elif 'dedication' in classes:
            return self._process_topic('dedication')
        elif 'abstract' in classes:
            return self._process_topic('abstract')
        else:
            return super().build_flowable()


class Rubric(DocutilsBodyNode):
    def build_flowable(self):
        return rt.Paragraph(self.process_content(), style='rubric')


class Sidebar(DocutilsGroupingNode):
    style = 'sidebar'


class Section(DocutilsGroupingNode):
    grouped_flowables_class = rt.Section


class Paragraph(DocutilsBodyNode):
    style = None

    def build_flowable(self):
        return rt.Paragraph(self.process_content(), style=self.style)


class Compound(DocutilsGroupingNode):
    pass


class Title(DocutilsBodyNode, DocutilsInlineNode):
    def build_flowable(self):
        if isinstance(self.parent, Document):
            return rt.SetMetadataFlowable(title=self.process_content())
        elif isinstance(self.parent, Section):
            try:
                kwargs = dict(custom_label=self.generated.build_styled_text())
            except AttributeError:
                kwargs = dict()
            return rt.Heading(self.process_content(), **kwargs)
        else:
            return rt.Paragraph(self.process_content(), style='title')


class Subtitle(DocutilsBodyNode):
    def build_flowable(self):
        return rt.SetMetadataFlowable(subtitle=self.process_content())


class Math_Block(DocutilsBodyNode):
    style = 'math'

    def build_flowables(self):
        yield rt.WarnFlowable("The 'math' directive is not yet supported")
        yield rt.Paragraph(self.process_content(), style=self.style)


class Admonition(DocutilsGroupingNode):
    grouped_flowables_class = rt.Admonition

    def children_flowables(self, skip_first=0):
        try:
            self.title
            return super().children_flowables(skip_first=1)
        except AttributeError:
            return super().children_flowables()

    def build_flowable(self):
        admonition_type = self.__class__.__name__.lower()
        try:
            custom_title = self.title.styled_text()
        except AttributeError:
            custom_title = None
        return super().build_flowable(type=admonition_type, title=custom_title)


class Attention(Admonition):
    pass


class Caution(Admonition):
    pass


class Danger(Admonition):
    pass


class Error(Admonition):
    pass


class Hint(Admonition):
    pass


class Important(Admonition):
    pass


class Note(Admonition):
    pass


class Tip(Admonition):
    pass


class Warning(Admonition):
    pass


class Generated(DocutilsInlineNode):
    def styled_text(self):
        return None

    def build_styled_text(self):
        return self.process_content()


class Emphasis(Inline):
    style = 'emphasis'


class Strong(Inline):
    style = 'strong'


class Title_Reference(DocutilsInlineNode):
    style = 'title reference'


class Literal(Inline):
    style = 'monospaced'


class Math(Inline):
    style = 'math'

    def build_styled_text(self):
        return (rt.WarnInline("The 'math' role is not yet supported")
                + super().build_styled_text())


class Superscript(DocutilsInlineNode):
    def build_styled_text(self):
        return rt.Superscript(self.process_content())


class Subscript(DocutilsInlineNode):
    def build_styled_text(self):
        return rt.Subscript(self.process_content())


class Problematic(DocutilsBodyNode, DocutilsInlineNode):
    def build_styled_text(self):
        return rt.SingleStyledText(self.text, style='error')

    def build_flowable(self):
        return rt.DummyFlowable()


class Literal_Block(DocutilsBodyNode):
    lexer_getter = None

    @property
    def language(self):
        classes = self.get('classes')
        if classes and classes[0] == 'code':    # .. code::
            return classes[1]
        return None                             # literal block (double colon)

    def build_flowable(self):
        return rt.CodeBlock(self.text, language=self.language,
                            lexer_getter=self.lexer_getter)


class Block_Quote(DocutilsGroupingNode):
    style = 'block quote'


class Attribution(Paragraph):
    style = 'attribution'

    def process_content(self, style=None):
        return '\N{EM DASH}' + super().process_content(style)


class Line_Block(Paragraph):
    style = 'line block'

    def _process_block(self, line_block):
        for child in line_block.getchildren():
            try:
                yield child.styled_text()
            except AttributeError:
                for line in self._process_block(child):
                    yield rt.Tab() + line

    def process_content(self, style=None):
        lines = self._process_block(self)
        return intersperse(lines, rt.Newline())


class Line(DocutilsInlineNode):
    pass


class Doctest_Block(DocutilsBodyNode):
    def build_flowable(self):
        return rt.CodeBlock(self.text)


class Reference(DocutilsBodyNode, DocutilsInlineNode):
    @property
    def annotation(self):
        if self.get('refid'):
            return rt.NamedDestinationLink(self.get('refid'))
        elif self.get('refuri'):
            return rt.HyperLink(self.get('refuri'))

    def build_styled_text(self):
        annotation = self.annotation
        content = self.process_content()
        if annotation is None:
            return rt.MixedStyledText(content, style='broken link')
        style = ('external link' if annotation.type == 'URI'
                 else 'internal link')
        return rt.AnnotatedText(content, annotation, style=style)

    def build_flowable(self):
        children = self.getchildren()
        assert len(children) == 1
        image = self.image.flowable()
        image.annotation = self.annotation
        return image


class Footnote(DocutilsBodyNode):
    def flowables(self):
        note, = super().flowables()
        yield rt.RegisterNote(note)

    def build_flowable(self):
        return rt.Note(rt.StaticGroupedFlowables(self.children_flowables(1)))


class Label(DocutilsBodyNode):
    def build_flowable(self):
        return rt.DummyFlowable()


class Footnote_Reference(DocutilsInlineNode):
    style = 'footnote'

    def build_styled_text(self):
        return rt.NoteMarkerByID(self['refid'],
                                 custom_label=self.process_content(),
                                 style=self.style)


class Citation(Footnote):
    pass


class Citation_Reference(Footnote_Reference):
    style = 'citation'


class Substitution_Definition(DocutilsBodyNode):
    def build_flowable(self):
        label, = self.node.attributes['names']
        content = self.process_content()
        return rt.SetUserStringFlowable(label, content)


class Target(DocutilsBodyNode, DocutilsInlineNode):
    def build_styled_text(self):
        # TODO: what about refid?
        try:
            destination = rt.NamedDestination(*self._ids)
            return rt.AnnotatedText(self.process_content(), destination)
        except IndexError:
            return self.process_content()   # TODO: use refname?

    def build_flowable(self):
        return rt.AnchorFlowable()


class Enumerated_List(DocutilsGroupingNode):
    style = 'enumerated'
    grouped_flowables_class = rt.List

    def build_flowable(self):
        # TODO: handle different numbering styles
        start = self.attributes.get('start', 1)
        return super().build_flowable(start_index=start)

class Bullet_List(DocutilsGroupingNode):
    style = 'bulleted'
    grouped_flowables_class = rt.List

    def build_flowable(self):
        try:
            return super().build_flowable()
        except AttributeError:  # empty list
            return rt.DummyFlowable()


class List_Item(DocutilsGroupingNode):
    def build_flowable(self):
        return rt.ListItem(super().build_flowable())


class Definition_List(DocutilsGroupingNode):
    grouped_flowables_class = rt.DefinitionList


class Definition_List_Item(DocutilsBodyNode):
    def build_flowable(self):
        term_text = self.term.styled_text()
        try:
            for classifier in self.classifier:
                term_text += ' : ' + classifier.styled_text()
        except AttributeError:
            pass
        term = rt.StaticGroupedFlowables([rt.Paragraph(term_text)],
                                         style='definition term')
        return rt.LabeledFlowable(term, self.definition.flowable())


class Term(DocutilsInlineNode):
    def build_styled_text(self):
        content = self.process_content()
        if self._ids:
            destination = rt.NamedDestination(*self._ids)
            content = rt.AnnotatedText(content, destination)
        return content


class Classifier(DocutilsInlineNode):
    def build_styled_text(self):
        return self.process_content('classifier')


class Definition(DocutilsGroupingNode):
    style = 'definition'


class Field_List(DocutilsGroupingNode):
    grouped_flowables_class = rt.DefinitionList
    style = 'field list'


class Field(DocutilsBodyNode):
    @property
    def name(self):
        return self.field_name.text

    @property
    def value(self):
        return self.field_body.flowable()

    def build_flowable(self):
        label = rt.Paragraph(self.field_name.styled_text(), style='field name')
        return rt.LabeledFlowable(label, self.field_body.flowable())


class Field_Name(DocutilsInlineNode):
    pass


class Field_Body(DocutilsGroupingNode):
    pass


class Option_List(DocutilsGroupingNode):
    grouped_flowables_class = rt.DefinitionList
    style = 'option list'


class Option_List_Item(DocutilsBodyNode):
    def build_flowable(self):
        return rt.LabeledFlowable(self.option_group.flowable(),
                                  self.description.flowable(), style='option')


class Option_Group(DocutilsBodyNode):
    def build_flowable(self):
        options = (option.styled_text() for option in self.option)
        return rt.Paragraph(intersperse(options, ', '), style='option_group')


class Option(DocutilsInlineNode):
    def build_styled_text(self):
        text = self.option_string.styled_text()
        try:
            delimiter = rt.MixedStyledText(self.option_argument['delimiter'],
                                           style='option_string')
            text += delimiter + self.option_argument.styled_text()
        except AttributeError:
            pass
        return rt.MixedStyledText(text)


class Option_String(DocutilsInlineNode):
    def build_styled_text(self):
        return rt.MixedStyledText(self.process_content(), style='option_string')


class Option_Argument(DocutilsInlineNode):
    def build_styled_text(self):
        return rt.MixedStyledText(self.process_content(), style='option_arg')


class Description(DocutilsGroupingNode):
    pass


class Image(DocutilsBodyNode, DocutilsInlineNode):
    @property
    def image_path(self):
        return self.get('uri')

    def build_flowable(self):
        width_string = self.get('width')
        align = self.get('align')
        return rt.Image(self.image_path, scale=self.get('scale', 100) / 100,
                        width=convert_quantity(width_string), align=align)

    ALIGN_TO_BASELINE = {'bottom': 0,
                         'middle': 50*PERCENT,
                         'top': 100*PERCENT}

    def build_styled_text(self):
        baseline = self.ALIGN_TO_BASELINE.get(self.get('align'))
        return rt.InlineImage(self.image_path, baseline=baseline)


class Figure(DocutilsGroupingNode):
    grouped_flowables_class = rt.Figure


class Caption(DocutilsBodyNode):
    def build_flowable(self):
        return rt.Caption(super().process_content())


class Legend(DocutilsGroupingNode):
    style = 'legend'


class Transition(DocutilsBodyNode):
    def build_flowable(self):
        return rt.HorizontalRule()


RE_LENGTH_PERCENT_UNITLESS = re.compile(r'^(?P<value>\d+)(?P<unit>[a-z%]*)$')

# TODO: warn on px or when no unit is supplied
DOCUTILS_UNIT_TO_DIMENSION = {'': PT,    # assume points for unitless quantities
                              'in': INCH,
                              'cm': CM,
                              'mm': MM,
                              'pt': PT,
                              'pc': PICA,
                              'px': DimensionUnit(1 / 100 * INCH, 'px'),
                              '%': PERCENT,
                              'em': None,
                              'ex': None}


def convert_quantity(quantity_string):
    if quantity_string is None:
        return None
    value, unit = RE_LENGTH_PERCENT_UNITLESS.match(quantity_string).groups()
    return float(value) * DOCUTILS_UNIT_TO_DIMENSION[unit]


class Table(DocutilsBodyNode):
    def build_flowable(self):
        tgroup = self.tgroup
        if 'colwidths-given' in self.get('classes'):
            column_widths = [int(colspec.get('colwidth'))
                             for colspec in tgroup.colspec]
        else:
            column_widths = None
        try:
            head = tgroup.thead.get_table_section()
        except AttributeError:
            head = None
        body = tgroup.tbody.get_table_section()
        align = self.get('align')
        width_string = self.get('width')
        return rt.Table(body, head=head,
                        align=None if align == 'default' else align,
                        width=convert_quantity(width_string),
                        column_widths=column_widths)

    def flowables(self):
        table, = super().flowables()
        try:
            caption = rt.Caption(self.title.process_content())
            table_with_caption = rt.TableWithCaption([caption, table])
            table_with_caption.classes.extend(self.get('classes'))
            yield table_with_caption
        except AttributeError:
            yield table


class TGroup(DocutilsNode):
    pass


class ColSpec(DocutilsNode):
    pass


class TableRowGroup(DocutilsNode):
    section_cls = None

    def get_table_section(self):
        return self.section_cls([row.get_row() for row in self.row])


class THead(TableRowGroup):
    section_cls = rt.TableHead


class TBody(TableRowGroup):
    section_cls = rt.TableBody


class Row(DocutilsNode):
    def get_row(self):
        return rt.TableRow([entry.flowable() for entry in self.entry])


class Entry(DocutilsGroupingNode):
    grouped_flowables_class = rt.TableCell

    def build_flowable(self):
        rowspan = int(self.get('morerows', 0)) + 1
        colspan = int(self.get('morecols', 0)) + 1
        return super().build_flowable(rowspan=rowspan, colspan=colspan)


class Raw(DocutilsBodyNode, DocutilsInlineNode):
    def build_styled_text(self):
        if self['format'] == 'rinoh':
            return rt.StyledText.from_string(self.text)

    def build_flowable(self):
        if self['format'] == 'rinoh':
            # TODO: Flowable.from_text(self.text)
            if self.text.startswith('ListOfFiguresSection'):
                return rt.ListOfFiguresSection()
            elif self.text == 'ListOfTablesSection':
                return rt.ListOfTablesSection()
            elif self.text == 'ListOfFigures(local=True)':
                return rt.ListOfFigures(local=True)
            elif self.text == 'ListOfTables(local=True)':
                return rt.ListOfTables(local=True)
            return rt.WarnFlowable("Unsupported raw pdf option: '{}'"
                                   .format(self.text))
        elif self['format'] == 'pdf':   # rst2pdf
            if self.text == 'PageBreak':
                return rt.PageBreak()
            return rt.WarnFlowable("Unsupported raw pdf option: '{}'"
                                   .format(self.text))
        return rt.DummyFlowable()


class Container(DocutilsGroupingNode):
    @property
    def set_id(self):
        return 'out-of-line' not in self['classes']

    def build_flowable(self, style=None, **kwargs):
        classes = self.get('classes')
        if 'literal-block-wrapper' in classes:
            return rt.CodeBlockWithCaption(self.children_flowables(),
                                           style=style or self.style, **kwargs)
        if 'out-of-line' in classes:
            names = self['names']
            if not names:
                raise MissingName('out-of-line container is missing a :name:'
                                  ' to reference it by')
            return rt.SetOutOfLineFlowables(names, self.children_flowables(),
                                            **kwargs)
        return super().build_flowable(style, **kwargs)


class MissingName(Exception):
    pass
