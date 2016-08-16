# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import unicodedata

from itertools import chain

from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

from sphinx.highlighting import lexers

from ...annotation import HyperLink, AnnotatedText
from ...flowable import LabeledFlowable
from ...index import IndexTerm, IndexTarget, InlineIndexTarget
from ...paragraph import Paragraph
from ...reference import Reference, REFERENCE
from ...structure import DefinitionList, DefinitionTerm, Definition, FieldList
from ...text import SingleStyledText, MixedStyledText
from ...util import intersperse
from ...warnings import warn

from ..rst import (DocutilsInlineNode, DocutilsBodyNode,
                   DocutilsGroupingNode, DocutilsDummyNode)
from ..rst.nodes import Admonition, Strong, Emphasis
from ..rst.nodes import Literal_Block as rst_Literal_Block


__all__ = ['Compact_Paragraph', 'Index', 'Pending_XRef', 'Literal_Emphasis',
           'Abbreviation', 'Download_Reference', 'SeeAlso', 'Glossary',
           'Start_of_File', 'Todo_Node', 'HighlightLang', 'Literal_Strong',
           'ProductionList', 'Production', 'TermSep', 'Desc', 'Desc_Signature',
           'Desc_Name', 'Desc_AddName', 'Desc_Type', 'Desc_ParameterList',
           'Desc_Parameter', 'Desc_Optional', 'Desc_Annotation', 'Desc_Content',
           'Desc_Returns', 'VersionModified', 'Tabular_Col_Spec',
           'AutoSummary_Table', 'Number_Reference']


# other paragraph-level nodes

class Compact_Paragraph(DocutilsGroupingNode):
    pass


# inline nodes

class Index(DocutilsBodyNode, DocutilsInlineNode):
    @property
    def _index_terms(self):
        for type, entry_name, target, ignored, key in self.get('entries'):
            if type == 'single':
                yield IndexTerm(*(n.strip() for n in entry_name.split(';')))
            elif type == 'pair':
                name, other_name = (n.strip() for n in entry_name.split(';'))
                yield IndexTerm(name, other_name)
                yield IndexTerm(other_name, name)
            elif type == 'triple':
                one, two, three = (n.strip() for n in entry_name.split(';'))
                yield IndexTerm(one, two + ' ' + three)
                yield IndexTerm(two, three + ', ' + one)
                yield IndexTerm(three, one + ' ' + two)
            else:
                raise NotImplementedError

    def build_flowable(self):
        return IndexTarget(list(self._index_terms))

    def build_styled_text(self):
        return InlineIndexTarget(list(self._index_terms))


class Pending_XRef(DocutilsInlineNode):
    def build_styled_text(self):
        raise NotImplementedError


class Literal_Emphasis(Emphasis):
    pass


class Literal_Block(rst_Literal_Block):
    @staticmethod
    def lexer_getter(text, language):
        # This is a partial copy of Sphinx's PygmentsBridge.highlight_block()
        if language in ('py', 'python'):
            if text.startswith('>>>'):
                # interactive session
                lexer = lexers['pycon']
            else:
                lexer = lexers['python']
        elif language in ('py3', 'python3', 'default'):
            if text.startswith('>>>'):
                lexer = lexers['pycon3']
            else:
                lexer = lexers['python3']
        elif language == 'guess':
            try:
                lexer = guess_lexer(text)
            except Exception:
                lexer = lexers['none']
        else:
            if language in lexers:
                lexer = lexers[language]
            else:
                try:
                    lexer = lexers[language] = get_lexer_by_name(language)
                except ClassNotFound:
                    if warn:
                        warn('Pygments lexer name %r is not known'
                             % language)
                        lexer = lexers['none']
                    else:
                        raise
                else:
                    lexer.add_filter('raiseonerror')
        return lexer

    @property
    def language(self):
        if 'language' in self.attributes:    # (Sphinx)    .. code-block::
            return self.get('language')
        else:                                # (docutils)
            return super().language


class Abbreviation(DocutilsInlineNode):
    def build_styled_text(self):
        result = self.process_content(style='abbreviation')
        # TODO: only show the explanation the first time
        # (needs support at Document level)
        try:
            result += ' (' + self.get('explanation') + ')'
        except KeyError:
            pass
        return result


class Download_Reference(DocutilsInlineNode):
    def build_styled_text(self):
        try:
            # TODO: (optionally) embed the file in the PDF
            link = HyperLink(self.get('reftarget'))
            return AnnotatedText(self.process_content(), link,
                                 style='download link')
        except KeyError:
            return super().build_styled_text()


# admonitions

class SeeAlso(Admonition):
    pass


class VersionModified(DocutilsGroupingNode):
    pass


# special nodes

class Glossary(DocutilsGroupingNode):
    style = 'glossary'


class Start_of_File(DocutilsGroupingNode):
    def build_flowable(self, **kwargs):
        return super().build_flowable(id='%' + self.get('docname'), **kwargs)


class Todo_Node(Admonition):
    pass


class HighlightLang(DocutilsDummyNode):  # these are handled by RinohBuilder
    pass


class Literal_Strong(Strong):
    def build_styled_text(self):
        return SingleStyledText(self.text, style='literal strong')


# toctree nodes are processed by the Sphinx builder

NO_BREAK_SPACE = unicodedata.lookup('NO-BREAK SPACE')

class ProductionList(DocutilsBodyNode):
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


class Production(DocutilsBodyNode):
    def build_flowable(self):
        return Paragraph(self.get('tokenname'), style='token')


class TermSep(DocutilsInlineNode):
    def build_styled_text(self):
        return SingleStyledText(', ', style='term separator')


# domain-specific object descriptions

class Desc(DocutilsBodyNode):
    def build_flowable(self):
        sigs = [sig.flowable() for sig in self.desc_signature]
        desc = self.desc_content.flowable()
        return DefinitionList([(DefinitionTerm(sigs), desc)],
                              style='object description')


class Desc_Signature(DocutilsBodyNode):
    def build_flowable(self):
        return Paragraph(self.process_content())


class Desc_Name(DocutilsInlineNode):
    style = 'main object name'


class Desc_AddName(DocutilsInlineNode):
    style = 'additional name part'


class Desc_Type(DocutilsInlineNode):
    style = 'type'


class Desc_ParameterList(DocutilsInlineNode):
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


class Desc_Parameter(DocutilsInlineNode):
    def build_styled_text(self):
        style = 'parameter'
        if self.get('noemph'):
            style = 'noemph ' + style
        return self.process_content(style=style)


class Desc_Optional(DocutilsInlineNode):
    def build_styled_text(self):
        return (SingleStyledText(' [, ', style='brackets')
                + self.process_content(style='optional')
                + SingleStyledText(' ] ', style='brackets'))


class Desc_Annotation(DocutilsInlineNode):
    style = 'annotation'


class Desc_Content(DocutilsGroupingNode):
    grouped_flowables_class = Definition


class Desc_Returns(DocutilsInlineNode):
    style = 'returns'

    def build_styled_text(self):
        arrow = SingleStyledText(unicodedata.lookup('RIGHTWARDS ARROW'),
                                 style='returns arrow')
        return arrow + ' ' + super().build_styled_text()



# not listed in "Doctree node classes added by Sphinx"

class Tabular_Col_Spec(DocutilsDummyNode):
    pass


class AutoSummary_Table(DocutilsGroupingNode):
    pass


class Number_Reference(DocutilsInlineNode):
    def build_styled_text(self):
        return Reference(self.get('refid'), REFERENCE, style='link')


class Footnotes_Rubric(DocutilsDummyNode):
    """A custom rinohtype-specific node that allows easily excluding footnote
    rubrics from the output"""
