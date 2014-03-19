
import rinoh as rt

from . import CustomElement, NestedElement, GroupingElement


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
    def parse(self, level=1):
        for element in self.getchildren():
            if isinstance(element, Title):
                elem = element.process(level=level, id=self.get('ids', None)[0])
            elif type(element) == Section:
                elem = element.process(level=level + 1)
            else:
                elem = element.process()
            if isinstance(elem, rt.Flowable):
                yield elem
            else:
                for flw in elem:
                    yield flw


class Paragraph(NestedElement):
    def parse(self):
        return rt.Paragraph(super().process_content())


class Title(CustomElement):
    def parse(self, level=None, id=None):
        if level is None:
            return rt.Paragraph(self.text, style='title')
        else:
            return rt.Heading(self.text, level=level, id=id)


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


class Literal_Block(CustomElement):
    def parse(self):
        return rt.Paragraph(rt.LiteralText(self.text), style='literal')


class Block_Quote(NestedElement):
    def parse(self):
        return rt.Paragraph(super().process_content(), style='block quote')


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
        # TODO: fix docutils so that each node has a reference to document
        for footnote in self.node.parent.document.autofootnotes:
            if footnote['auto'] == self.node['auto']:
                nodes = self.map_node(footnote).getchildren()[1:]  # drop label
                content = [node.parse() for node in nodes]
                return rt.NoteMarker(rt.StaticGroupedFlowables(content))
        raise KeyError('Footnote {} not found.'.format(self.node['auto']))


class Substitution_Definition(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Target(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


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
        return rt.StaticGroupedFlowables([field.process()
                                          for field in self.field])


class Field(CustomElement):
    def parse(self):
        return rt.LabeledFlowable(self.field_name.process(),
                                  self.field_body.process())


class Field_Name(NestedElement):
    def parse(self):
        return rt.Paragraph(self.process_content())


class Field_Body(GroupingElement):
    pass


class Image(CustomElement):
    def parse(self):
        return rt.Image(self.get('uri').rsplit('.png', 1)[0])
