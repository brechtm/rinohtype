# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import unicodedata

from itertools import chain

from ...annotation import HyperLink, AnnotatedText
from ...flowable import LabeledFlowable
from ...paragraph import Paragraph
from ...reference import Reference, REFERENCE
from ...structure import DefinitionList, DefinitionTerm, FieldList
from ...text import SingleStyledText, MixedStyledText
from ...util import intersperse

from ..rst import (ReStructuredTextInlineNode, ReStructuredTextBodyNode,
                   ReStructuredTextGroupingNode, ReStructuredTextDummyNode)
from ..rst.nodes import Admonition, AdmonitionBase, Strong, Emphasis


__all__ = ['Compact_Paragraph', 'Index', 'Pending_XRef', 'Literal_Emphasis',
           'Abbreviation', 'Download_Reference', 'SeeAlso', 'Glossary',
           'Start_of_File', 'Todo_Node', 'HighlightLang', 'Literal_Strong',
           'ProductionList', 'Production', 'TermSep', 'Desc', 'Desc_Signature',
           'Desc_Name', 'Desc_AddName', 'Desc_Type', 'Desc_ParameterList',
           'Desc_Parameter', 'Desc_Optional', 'Desc_Annotation', 'Desc_Content',
           'Desc_Returns', 'VersionModified', 'Tabular_Col_Spec',
           'AutoSummary_Table', 'Number_Reference']


# other paragraph-level nodes

class Compact_Paragraph(ReStructuredTextGroupingNode):
    pass


# inline nodes

class Index(ReStructuredTextDummyNode):
    def build_styled_text(self):
        for entrytype, entryname, target, ignored in self.get('entries'):
            # TODO: generate index
            pass
        return None


class Pending_XRef(ReStructuredTextInlineNode):
    def build_styled_text(self):
        raise NotImplementedError


class Literal_Emphasis(Emphasis):
    pass


class Abbreviation(ReStructuredTextInlineNode):
    def build_styled_text(self):
        result = self.process_content(style='abbreviation')
        # TODO: only show the explanation the first time
        # (needs support at Document level)
        try:
            result += ' (' + self.get('explanation') + ')'
        except KeyError:
            pass
        return result


class Download_Reference(ReStructuredTextInlineNode):
    def build_styled_text(self):
        try:
            # TODO: (optionally) embed the file in the PDF
            link = HyperLink(self.get('reftarget'))
            return AnnotatedText(self.process_content(), link,
                                 style='download link')
        except KeyError:
            return super().build_styled_text()


# admonitions

class SeeAlso(AdmonitionBase):
    title = 'See also'


class VersionModified(ReStructuredTextGroupingNode):
    pass


# special nodes

class Glossary(ReStructuredTextGroupingNode):
    style = 'glossary'


class Start_of_File(ReStructuredTextGroupingNode):
    def build_flowable(self, **kwargs):
        return super().build_flowable(id='%' + self.get('docname'), **kwargs)


class Todo_Node(Admonition):
    pass


class HighlightLang(ReStructuredTextDummyNode):
    pass


class Literal_Strong(Strong):
    pass


# toctree nodes are processed by the Sphinx builder

NO_BREAK_SPACE = unicodedata.lookup('NO-BREAK SPACE')

class ProductionList(ReStructuredTextBodyNode):
    def build_flowable(self):
        items = []
        productions = iter(self.production)
        production = next(productions)
        while production is not None:
            token_label = production.flowable()
            definition_text = ['::=' + production.text]
            for production in productions:
                token_name = production.get('tokenname')
                if token_name:
                    break
                else:
                    definition_text.append('   ' + production.text)
            else:
                production = None
            token_definition = Paragraph('\n'.join(definition_text)
                                         .replace(' ', NO_BREAK_SPACE),
                                         style='definition')
            item = LabeledFlowable(token_label, token_definition,
                                   style='production')
            items.append(item)
        return FieldList(items, style='production list')


class Production(ReStructuredTextBodyNode):
    def build_flowable(self):
        return Paragraph(self.get('tokenname'), style='token')


class TermSep(ReStructuredTextInlineNode):
    def build_styled_text(self):
        return SingleStyledText(', ', style='term separator')


# domain-specific object descriptions

class Desc(ReStructuredTextBodyNode):
    def build_flowable(self):
        sigs = [sig.flowable() for sig in self.desc_signature]
        desc = self.desc_content.flowable()
        return DefinitionList([(DefinitionTerm(sigs), desc)],
                              style='object description')


class Desc_Signature(ReStructuredTextBodyNode):
    def build_flowable(self):
        return Paragraph(self.process_content())


class Desc_Name(ReStructuredTextInlineNode):
    style = 'main object name'


class Desc_AddName(ReStructuredTextInlineNode):
    style = 'additional name part'


class Desc_Type(ReStructuredTextInlineNode):
    style = 'type'


class Desc_ParameterList(ReStructuredTextInlineNode):
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


class Desc_Parameter(ReStructuredTextInlineNode):
    def build_styled_text(self):
        style = 'parameter'
        if self.get('noemph'):
            style = 'noemph ' + style
        return self.process_content(style=style)


class Desc_Optional(ReStructuredTextInlineNode):
    def build_styled_text(self):
        return (SingleStyledText(' [, ', style='brackets')
                + self.process_content(style='optional')
                + SingleStyledText(' ] ', style='brackets'))


class Desc_Annotation(ReStructuredTextInlineNode):
    style = 'annotation'


class Desc_Content(ReStructuredTextGroupingNode):
    pass


class Desc_Returns(ReStructuredTextInlineNode):
    style = 'returns'

    def build_styled_text(self):
        arrow = SingleStyledText(unicodedata.lookup('RIGHTWARDS ARROW'),
                                 style='returns arrow')
        return arrow + ' ' + super().build_styled_text()



# not listed in "Doctree node classes added by Sphinx"

class Tabular_Col_Spec(ReStructuredTextDummyNode):
    pass


class AutoSummary_Table(ReStructuredTextGroupingNode):
    pass


class Number_Reference(ReStructuredTextInlineNode):
    def build_styled_text(self):
        return Reference(self.get('refid'), REFERENCE, style='link')
