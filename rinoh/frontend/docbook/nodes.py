# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from . import CustomElement, BodyElement, InlineElement, GroupingElement

from ... import styleds


class Article(BodyElement):
    pass


class Info(BodyElement):
    def build_flowable(self):
        doc_info = {field.key: field.value for field in self.getchildren()}
        return styleds.SetMetadataFlowable(**doc_info)


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


class Para(BodyElement):
    def build_flowable(self):
        return styleds.Paragraph(super().process_content())


class Emphasis(InlineElement):
    style = 'emphasis'


class Acronym(InlineElement):
    style = 'acronym'


class Title(BodyElement, TextInfoField):
    name = 'title'

    def build_flowable(self):
        return styleds.Heading(self.process_content())


class Section(GroupingElement):
    grouped_flowables_class = styleds.Section


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
