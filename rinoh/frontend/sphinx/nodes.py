# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.
from itertools import chain

from ...flowable import DummyFlowable
from ...paragraph import Paragraph
from ...reference import Reference, REFERENCE
from ...structure import DefinitionList, DefinitionTerm
from ...text import SingleStyledText, MixedStyledText
from ...util import intersperse

from ..rst import BodyElement, InlineElement, GroupingElement
from ..rst.nodes import Admonition, AdmonitionBase, Strong, Inline


__all__ = ['Compact_Paragraph', 'Index', 'SeeAlso', 'Glossary', 'Start_of_File',
           'Todo_Node', 'HighlightLang', 'Literal_Strong', 'Desc',
           'Desc_Signature', 'Desc_Name', 'Desc_AddName', 'Desc_ParameterList',
           'Desc_Parameter', 'Desc_Optional', 'Desc_Annotation', 'Desc_Content',
           'VersionModified', 'Tabular_Col_Spec', 'AutoSummary_Table',
           'Number_Reference']


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
        return super().build_flowable(id='%' + self.get('docname'), **kwargs)


class Todo_Node(Admonition):
    pass


class HighlightLang(BodyElement):
    def build_flowable(self):
        return DummyFlowable()


class Literal_Strong(Strong):
    pass


class Desc(BodyElement):
    def build_flowable(self):
        sigs = [sig.flowable() for sig in self.desc_signature]
        desc = self.desc_content.flowable()
        return DefinitionList([(DefinitionTerm(sigs), desc)],
                              style='object description')


class Desc_Signature(BodyElement):
    def build_flowable(self):
        return Paragraph(self.process_content())


class Desc_Name(Inline):
    style = 'main object name'


class Desc_AddName(Inline):
    style = 'additional name part'


class Desc_ParameterList(InlineElement):
    def build_styled_text(self):
        try:
            params = intersperse((param.styled_text()
                                  for param in self.desc_parameter), ', ')
        except AttributeError:
            params = ()
        try:
            params = chain(params, (self.desc_optional.styled_text(), ))
        except AttributeError:
            pass
        return (SingleStyledText(' ( ', style='parentheses')
                + MixedStyledText(params, style='parameter list')
                + SingleStyledText(' ) ', style='parentheses'))


class Desc_Parameter(Inline):
    style = 'parameter'


class Desc_Optional(InlineElement):
    def build_styled_text(self):
        return (SingleStyledText(' [, ', style='brackets')
                + self.process_content(style='optional')
                + SingleStyledText(' ] ', style='brackets'))


class Desc_Annotation(Inline):
    style = 'annotation'


class Desc_Content(GroupingElement):
    pass


class Tabular_Col_Spec(BodyElement):
    def build_flowable(self):
        return DummyFlowable()


class AutoSummary_Table(GroupingElement):
    pass


class Number_Reference(Inline):
    def build_styled_text(self):
        return Reference(self.get('refid'), REFERENCE, style='link')
