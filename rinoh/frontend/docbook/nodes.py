# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from . import (CustomElement, BodyElement, BodySubElement, InlineElement,
               GroupingElement)

from ... import styleds
from ...annotation import NamedDestinationLink
from rinoh.reference import TITLE, PAGE


class DocumentRoot(BodyElement):
    pass


class Article(DocumentRoot):
    pass


class Book(DocumentRoot):
    pass


class Info(BodyElement):
    def build_flowable(self):
        doc_info = {field.key: field.value for field in self.getchildren()}
        return styleds.SetMetadataFlowable(**doc_info)


class ArticleInfo(Info):
    pass


class InfoField(CustomElement):
    @property
    def key(self):
        return self.node.tag[self.node.tag.find('}') + 1:]


class TextInfoField(InfoField):
    @property
    def value(self):
        return self.process_content()


class GroupingInfoField(GroupingElement, InfoField):
    @property
    def value(self):
        return self.flowable()


class Author(TextInfoField):
    pass


class PersonName(InlineElement):
    pass


class FirstName(InlineElement):
    pass


class Surname(InlineElement):
    pass


class Affiliation(InlineElement):
    pass


class Address(InlineElement):
    pass


class EMail(InlineElement):
    pass


class Copyright(TextInfoField):
    pass


class Year(InlineElement):
    pass


class Holder(InlineElement):
    pass


class Abstract(GroupingInfoField):
    pass


class VolumeNum(TextInfoField):
    pass


class Para(BodyElement):
    def build_flowables(self):
        paragraph = [self.text]
        for child in self.getchildren():
            try:
                paragraph.append(child.styled_text())
            except AttributeError:
                if paragraph and paragraph[0]:
                    yield styleds.Paragraph(paragraph)
                paragraph = []
                for flowable in child.flowables():
                    yield flowable
        if paragraph and paragraph[0]:
            yield styleds.Paragraph(paragraph)


class Emphasis(InlineElement):
    style = 'emphasis'


class Acronym(InlineElement):
    style = 'acronym'


class Title(BodyElement, TextInfoField):
    name = 'title'

    def build_flowable(self):
        if isinstance(self.parent, DocumentRoot):
            return styleds.SetMetadataFlowable(title=self.process_content())
        return styleds.Heading(self.process_content())


class Section(GroupingElement):
    grouped_flowables_class = styleds.Section


class Chapter(Section):
    pass


class Sect1(Section):
    pass


class Sect2(Section):
    pass


class Sect3(Section):
    pass


class Sect4(Section):
    pass


class Sect5(Section):
    pass


class MediaObject(BodyElement):
    def build_flowables(self):
        for flowable in self.imageobject.flowables():
            yield flowable


class ImageObject(BodyElement):
    def build_flowable(self):
        return styleds.Image(self.imagedata.get('fileref'))


class ImageData(CustomElement):
    pass


class TextObject(Para):
    pass


class Phrase(InlineElement):
    pass


class OrderedList(BodyElement):
    def build_flowable(self):
        return styleds.List([item.process() for item in self.listitem],
                            style='enumerated')


class ItemizedList(BodyElement):
    def build_flowable(self):
        return styleds.List([item.process() for item in self.listitem],
                            style='bulleted')


class ListItem(BodySubElement):
    def process(self):
        return self.children_flowables()


class XRef(BodyElement):
    def build_flowable(self):
        section_ref = styleds.Reference(self.get('linkend'), type=TITLE)
        page_ref = styleds.Reference(self.get('linkend'), type=PAGE)
        return styleds.Paragraph(section_ref + ' on page ' + page_ref)

        link = NamedDestinationLink(self.get('linkend'))
        return styleds.Paragraph(styleds.AnnotatedText('test', link,
                                                       style='internal link'))
