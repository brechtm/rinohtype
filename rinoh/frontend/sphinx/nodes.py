# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ...decoration import Framed
from ...flowable import DummyFlowable, PageBreak
from ...paragraph import Paragraph
from ...structure import DefinitionList, DefinitionTerm
from ...text import SingleStyledText
from ..rst import BodyElement, InlineElement, GroupingElement
from ..rst.nodes import AdmonitionBase, Strong, Inline


__all__ = ['Compact_Paragraph', 'Index', 'SeeAlso', 'Glossary', 'Start_of_File',
           'Todo_Node', 'Raw', 'HighlightLang', 'Literal_Strong',
           'Desc', 'Desc_Signature', 'Desc_Name', 'Desc_ParameterList',
           'Desc_Parameter', 'Desc_Optional', 'Desc_Content',
           'VersionModified', 'Tabular_Col_Spec', 'AutoSummary_Table']


class Compact_Paragraph(GroupingElement):
    pass


class Index(BodyElement, InlineElement):
    def build_styled_text(self):
        return SingleStyledText('')

    def build_flowable(self):
        return DummyFlowable()


class SeeAlso(AdmonitionBase):
    title = 'See also'


class VersionModified(GroupingElement):
    pass


class Glossary(GroupingElement):
    pass


class Start_of_File(GroupingElement):
    pass


class Todo_Node(GroupingElement):
    def flowable(self):
        return Framed(super().flowable())


class Raw(BodyElement):
    def build_flowable(self):
        if self.text == 'PageBreak':
            return PageBreak()
        else:
            return DummyFlowable()


class HighlightLang(BodyElement):
    def build_flowable(self):
        return DummyFlowable()


class Literal_Strong(Strong):
    pass


class Desc(BodyElement):
    def build_flowable(self):
        return DefinitionList([(self.desc_signature.flowable(),
                                self.desc_content.flowable())])


class Desc_Signature(BodyElement):
    def build_flowable(self):
        return Paragraph(self.desc_name.styled_text())


class Desc_Name(Inline):
    pass


class Desc_ParameterList(InlineElement):
    def build_styled_text(self):
        return [parameter.process() for parameter in self.desc_parameter]


class Desc_Parameter(Inline):
    pass


class Desc_Optional(Desc_ParameterList):
    pass


class Desc_Content(GroupingElement):
    pass


class Tabular_Col_Spec(BodyElement):
    def build_flowable(self):
        return DummyFlowable()


class AutoSummary_Table(GroupingElement):
    def build_flowable(self):
        return DummyFlowable()
