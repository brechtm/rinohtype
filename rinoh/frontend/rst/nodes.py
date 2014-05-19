
import rinoh as rt

from . import CustomElement, InlineElement, NestedElement, GroupingElement
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


class Topic(GroupingElement):
    style = 'topic'


class Rubric(NestedElement):
    def parse(self):
        return rt.Paragraph(self.process_content(), style='rubric')


class Sidebar(GroupingElement):
    def parse(self):
        grouped_flowables = super().parse()
        return rt.Framed(grouped_flowables, style='sidebar')


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


class Compound(GroupingElement):
    pass


class Title(CustomElement):
    def parse(self):
        if isinstance(self.parent, Section):
            return rt.Heading(self.text)
        else:
            return rt.Paragraph(self.text, 'title')


class Subtitle(CustomElement):
    def parse(self):
        return rt.Paragraph(self.text, 'subtitle')


class Admonition(GroupingElement):
    def parse(self):
        return rt.Framed(super().parse(), style='admonition')


class AdmonitionBase(GroupingElement):
    title = None

    def parse(self):
        title_par = rt.Paragraph(self.title, style='title')
        content = rt.StaticGroupedFlowables([title_par, super().parse()])
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


class Emphasis(InlineElement):
    def parse(self):
        return rt.Emphasized(self.text)


class Strong(InlineElement):
    def parse(self):
        return rt.Bold(self.text)


class Title_Reference(NestedElement):
    def parse(self):
        return rt.Italic(self.text)


class Literal(InlineElement):
    def parse(self):
        return rt.LiteralText(self.text, style='monospaced')


class Superscript(InlineElement):
    def parse(self):
        return rt.Superscript(self.process_content())


class Subscript(InlineElement):
    def parse(self):
        return rt.Subscript(self.process_content())


class Problematic(NestedElement):
    def parse(self, inline=False):
        if inline:
            return rt.SingleStyledText(self.text, style='error')
        else:
            return rt.DummyFlowable()


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


class Reference(NestedElement):
    def parse(self, inline=False):
        if not inline:
            children = self.getchildren()
            assert len(children) == 1
            return self.image.parse()
        else:
            return super().parse()


class Footnote(CustomElement):
    def parse(self):
        assert len(self.node['ids']) == 1
        note_id = self.node['ids'][0]
        content = [node.process() for node in self.getchildren()[1:]]
        note = rt.Note(rt.StaticGroupedFlowables(content), id=note_id)
        return rt.RegisterNote(note)


class Label(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Footnote_Reference(InlineElement):
    def parse(self):
        return rt.NoteMarker(self.node['refid'])




class Substitution_Definition(CustomElement):
    def parse(self):
        return rt.DummyFlowable()


class Target(NestedElement):
    def parse(self, inline=False):
        if inline:
            return self.process_content()
        else:
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
            delimiter = rt.MixedStyledText(self.option_argument['delimiter'],
                                           style='option_string')
            text += delimiter + self.option_argument.process()
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
