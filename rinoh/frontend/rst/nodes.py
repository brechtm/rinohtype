
from itertools import chain

import rinoh as rt

from . import CustomElement, NestedElement, GroupingElement
from ...util import intersperse


class Text(CustomElement):
    def process(self, *args, **kwargs):
        return self.text


class Document(CustomElement):
    pass


class DocInfo(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class System_Message(CustomElement):
    def parse(self, *args, **kwargs):
        return rt.WarnFlowable(self.text)


class Comment(CustomElement):
    def process(self, *args, **kwargs):
        return rt.DummyFlowable()


class Topic(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Section(CustomElement):
    def parse(self):
        flowables = []
        for element in self.getchildren():
            flowable = element.process()
            flowables.append(flowable)
        return rt.Section(flowables, id=self.get('ids', None)[0])


class Paragraph(NestedElement):
    def parse(self):
        return rt.Paragraph(super().process_content())


class Title(CustomElement):
    def parse(self):
        if isinstance(self.parent, Section):
            return rt.Heading(self.text)
        else:
            return rt.Paragraph(self.text, 'title')


class Subtitle(CustomElement):
    def parse(self):
        return rt.Paragraph(self.text, 'subtitle')


class Note(GroupingElement):
    def parse(self):
        content = rt.StaticGroupedFlowables([rt.Paragraph(rt.Bold('Note')),
                                             super().parse()])
        return rt.Framed(content)


class Tip(GroupingElement):
    def parse(self):
        content = rt.StaticGroupedFlowables([rt.Paragraph(rt.Bold('Tip')),
                                             super().parse()])
        return rt.Framed(content)


class Emphasis(NestedElement):
    def parse(self):
        return rt.Emphasized(self.text)


class Strong(CustomElement):
    def parse(self):
        return rt.Bold(self.text)


class Title_Reference(NestedElement):
    def parse(self):
        return rt.Italic(self.text)


class Literal(CustomElement):
    def parse(self):
        return rt.LiteralText(self.text, style='monospaced')


class Superscript(NestedElement):
    def parse(self):
        return rt.Superscript(self.process_content())


class Subscript(NestedElement):
    def parse(self):
        return rt.Subscript(self.process_content())


class Problematic(CustomElement):
    def parse(self):
        return rt.SingleStyledText(self.text, style='error')


class Literal_Block(CustomElement):
    def parse(self):
        return rt.Paragraph(rt.LiteralText(self.text), style='literal')


class Block_Quote(GroupingElement):
    style = 'block quote'


class Attribution(Paragraph):
    def parse(self):
        return rt.Paragraph('\N{EM DASH}' + self.process_content(),
                            style='attribution')


class Line_Block(GroupingElement):
    style = 'line block'


class Line(NestedElement):
    def parse(self):
        return rt.Paragraph(self.process_content() or '\n',
                            style='line block line')


class Doctest_Block(CustomElement):
    def parse(self):
        return rt.Paragraph(rt.LiteralText(self.text), style='literal')


class Reference(CustomElement):
    def parse(self):
        return self.text


class Footnote(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Label(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Footnote_Reference(NestedElement):
    def parse(self):
        footnote = self._find_matching_footnote()
        nodes = self.map_node(footnote).getchildren()[1:]  # drop label
        content = [node.parse() for node in nodes]
        return rt.NoteMarker(rt.StaticGroupedFlowables(content))

    def _find_matching_footnote(self):
        # TODO: fix docutils so that each node has a reference to document
        def get_document(node):
            return node.document or get_document(node.parent)

        docutils_document = get_document(self.node)
        for footnote in chain(docutils_document.autofootnotes,
                              docutils_document.symbol_footnotes,
                              docutils_document.footnotes):
            if self.node['refid'] in footnote['ids']:
                return footnote
        raise KeyError('Footnote {} not found.'.format(self.node['refid']))




class Substitution_Definition(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Target(NestedElement):
    def parse(self):
        return self.process_content() or rt.DummyFlowable()


class Enumerated_List(CustomElement):
    def parse(self):
        # TODO: handle different numbering styles
        return rt.List([item.process() for item in self.list_item],
                       style='enumerated')


class Bullet_List(CustomElement):
    def parse(self):
        return rt.List([item.process() for item in self.list_item],
                       style='bulleted')


class List_Item(NestedElement):
    def parse(self):
        return [item.process() for item in self.getchildren()]


class Definition_List(CustomElement):
    def parse(self):
        return rt.DefinitionList([item.process()
                                  for item in self.definition_list_item])

class Definition_List_Item(CustomElement):
    def parse(self):
        return (self.term.process(), self.definition.process())


class Term(NestedElement):
    def parse(self):
        return rt.MixedStyledText(self.process_content())


class Definition(GroupingElement):
    pass


class Field_List(CustomElement):
    def parse(self):
        return rt.FieldList([field.process() for field in self.field])


class Field(CustomElement):
    def parse(self):
        return rt.LabeledFlowable(self.field_name.process(),
                                  self.field_body.process())


class Field_Name(NestedElement):
    def parse(self):
        return rt.Paragraph(self.process_content(), style='field_name')


class Field_Body(GroupingElement):
    pass


class Option_List(CustomElement):
    def parse(self):
        return rt.FieldList([item.process() for item in self.option_list_item])


class Option_List_Item(CustomElement):
    def parse(self):
        return rt.LabeledFlowable(self.option_group.process(),
                                  self.description.process(),
                                  style='option')


class Option_Group(NestedElement):
    def parse(self):
        options = (option.process() for option in self.option)
        return rt.Paragraph(intersperse(options, ', '), style='option_group')


class Option(NestedElement):
    def parse(self):
        text = self.option_string.process()
        try:
            text += ' ' + self.option_argument.process()
        except AttributeError:
            pass
        return rt.MixedStyledText(text)


class Option_String(NestedElement):
    def parse(self):
        return rt.MixedStyledText(self.process_content(), style='option_string')


class Option_Argument(NestedElement):
    def parse(self):
        return rt.MixedStyledText(self.process_content(), style='option_arg')


class Description(GroupingElement):
    pass


class Image(CustomElement):
    def parse(self):
        return rt.Image(self.get('uri').rsplit('.png', 1)[0])


class Transition(CustomElement):
    def parse(self):
        return rt.HorizontalRule()
