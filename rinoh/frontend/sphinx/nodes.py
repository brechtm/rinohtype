# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ...decoration import Framed
from ...flowable import DummyFlowable, StaticGroupedFlowables
from ...structure import DefinitionList, DefinitionTerm
from ...text import SingleStyledText

from ..rst import BodyElement, InlineElement, GroupingElement
from ..rst.nodes import AdmonitionBase, Strong, Inline


__all__ = ['Compact_Paragraph', 'Index', 'SeeAlso', 'Glossary', 'Start_of_File',
           'Todo_Node', 'HighlightLang', 'Literal_Strong', 'Desc',
           'Desc_Signature', 'Desc_Name', 'Desc_AddName', 'Desc_ParameterList',
           'Desc_Parameter', 'Desc_Optional', 'Desc_Annotation', 'Desc_Content',
           'VersionModified', 'Tabular_Col_Spec', 'AutoSummary_Table']


class Compact_Paragraph(GroupingElement):
    pass


class Index(BodyElement, InlineElement):
    def build_styled_text(self):
        return None

    def build_flowable(self):
        return DummyFlowable()


class SeeAlso(AdmonitionBase):
    title = 'See also'


class VersionModified(GroupingElement):
    pass


class Glossary(GroupingElement):
    pass


class Start_of_File(GroupingElement):
    def build_flowable(self, **kwargs):
        return super().build_flowable(id=self.get('docname'), **kwargs)


class Todo_Node(GroupingElement):
    def flowable(self):
        return Framed(super().flowable())


class HighlightLang(BodyElement):
    def build_flowable(self):
        return DummyFlowable()


class Literal_Strong(Strong):
    pass


class Desc(BodyElement):
    def build_flowable(self):
        term = [sig.flowable() for sig in self.desc_signature]
        return DefinitionList([(StaticGroupedFlowables(term),
                                self.desc_content.flowable())])


class Desc_Signature(BodyElement):
    def build_flowable(self):
        return DefinitionTerm(self.process_content())


class Desc_Name(Inline):
    pass


class Desc_AddName(Inline):
    pass


class Desc_ParameterList(InlineElement):
    def build_styled_text(self):
        return '(' + self.process_content() + ')'


class Desc_Parameter(Inline):
    pass


class Desc_Optional(InlineElement):
    def build_styled_text(self):
        return '[, ' + self.process_content() + ']'


class Desc_Annotation(Inline):
    pass


class Desc_Content(GroupingElement):
    pass


class Tabular_Col_Spec(BodyElement):
    def build_flowable(self):
        return DummyFlowable()


class AutoSummary_Table(GroupingElement):
    pass
