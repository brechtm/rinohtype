# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from . import (DocBookNode, DocBookInlineNode, DocBookBodyNode,
               DocBookGroupingNode)

from ...reference import TITLE, PAGE

from ... import styleds


class DocumentRoot(DocBookBodyNode):
    pass


class Article(DocumentRoot):
    pass


class Book(DocumentRoot):
    pass


class Info(DocBookBodyNode):
    def build_flowable(self):
        doc_info = {field.key: field.value for field in self.getchildren()}
        return styleds.SetMetadataFlowable(**doc_info)


class ArticleInfo(Info):
    pass


class InfoField(DocBookNode):
    @property
    def key(self):
        return self.node.tag[self.node.tag.find('}') + 1:]


class TextInfoField(InfoField):
    @property
    def value(self):
        return self.process_content()


class GroupingInfoField(DocBookGroupingNode, InfoField):
    @property
    def value(self):
        return self.flowable()


class Author(TextInfoField):
    pass


class PersonName(DocBookInlineNode):
    pass


class FirstName(DocBookInlineNode):
    pass


class Surname(DocBookInlineNode):
    pass


class Affiliation(DocBookInlineNode):
    pass


class Address(DocBookInlineNode):
    pass


class EMail(DocBookInlineNode):
    pass


class Copyright(TextInfoField):
    pass


class Year(DocBookInlineNode):
    pass


class Holder(DocBookInlineNode):
    pass


class Abstract(GroupingInfoField):
    pass


class VolumeNum(TextInfoField):
    pass


class Para(DocBookGroupingNode):
    pass


class Emphasis(DocBookInlineNode):
    style = 'emphasis'


class Acronym(DocBookInlineNode):
    style = 'acronym'


class Title(DocBookBodyNode, TextInfoField):
    name = 'title'

    def build_flowable(self):
        if isinstance(self.parent, DocumentRoot):
            return styleds.SetMetadataFlowable(title=self.process_content())
        elif isinstance(self.parent, ListBase):
            return styleds.Paragraph(self.process_content())
        return styleds.Heading(self.process_content())


class Section(DocBookGroupingNode):
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


class MediaObject(DocBookBodyNode):
    def build_flowables(self):
        for flowable in self.imageobject.flowables():
            yield flowable


class ImageObject(DocBookBodyNode):
    def build_flowable(self):
        return styleds.Image(self.imagedata.get('fileref'))


class ImageData(DocBookNode):
    pass


class TextObject(Para):
    pass


class Phrase(DocBookInlineNode):
    pass



class ListBase(DocBookBodyNode):
    style = None

    def build_flowables(self):
        for child in self.getchildren():
            if isinstance(child, ListItem):
                break
            for flowable in child.flowables():
                yield flowable
        yield styleds.List([item.flowable() for item in self.listitem],
                           style=self.style)


class OrderedList(ListBase):
    style = 'enumerated'


class ItemizedList(ListBase):
    style = 'bulleted'


class ListItem(DocBookGroupingNode):
    pass


class XRef(DocBookBodyNode):
    def build_flowable(self):
        section_ref = styleds.Reference(self.get('linkend'), type=TITLE)
        page_ref = styleds.Reference(self.get('linkend'), type=PAGE)
        return styleds.Paragraph(section_ref + ' on page ' + page_ref)
