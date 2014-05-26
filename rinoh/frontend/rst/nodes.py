
import re
import unicodedata

import rinoh as rt

from . import BodyElement, BodySubElement, InlineElement, GroupingElement
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
        return rt.Section(flowables, id=self.get('ids', None)[0])


class Paragraph(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(super().process_content())


class Compound(GroupingElement):
    pass


class Title(BodyElement):
    def build_flowable(self):
        if isinstance(self.parent, Section):
            return rt.Heading(self.process_content())
        else:
            return rt.Paragraph(self.process_content(), 'title')


class Subtitle(BodyElement):
    def build_flowable(self):
        return rt.Paragraph(self.text, 'subtitle')


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
        refuri = self.get('refuri', None)
        if refuri:
            link = rt.HyperLink(refuri)
            return rt.AnnotatedText(self.process_content(), link, style='link')
        else:
            return self.process_content()

    def build_flowable(self):
        children = self.getchildren()
        assert len(children) == 1
        return self.image.flowable()


class Footnote(BodyElement):
    def build_flowable(self):
        assert len(self.node['ids']) == 1
        note_id = self.node['ids'][0]
        content = [node.flowable() for node in self.getchildren()[1:]]
        note = rt.Note(rt.StaticGroupedFlowables(content), id=note_id)
        return rt.RegisterNote(note)


class Label(BodyElement):
    def build_flowable(self):
        return rt.DummyFlowable()


class Footnote_Reference(InlineElement):
    def build_styled_text(self):
        return rt.NoteMarker(self.node['refid'])




class Substitution_Definition(BodyElement):
    def build_flowable(self):
        return rt.DummyFlowable()


class Target(BodyElement, InlineElement):
    def build_styled_text(self):
        return self.process_content()

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
        return (term, self.definition.flowable())


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
                                  self.description.flowable(),
                                  style='option')


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


class Transition(BodyElement):
    def build_flowable(self):
        return rt.HorizontalRule()
