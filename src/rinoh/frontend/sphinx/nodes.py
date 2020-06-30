# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import unicodedata

from itertools import chain

from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers.c_cpp import CLexer
from pygments.lexers.markup import RstLexer
from pygments.lexers.python import (PythonLexer, Python3Lexer,
                                    PythonConsoleLexer)
from pygments.lexers.special import TextLexer
from pygments.util import ClassNotFound

from ...annotation import HyperLink, AnnotatedText
from ...flowable import LabeledFlowable, StaticGroupedFlowables
from ...glossary import GlossaryTerm
from ...index import IndexTerm, IndexTarget, InlineIndexTarget
from ...paragraph import Paragraph
from ...reference import Reference
from ...structure import DefinitionList, List
from ...text import SingleStyledText, MixedStyledText
from ...util import intersperse
from ...warnings import warn

from ..rst import (DocutilsNode, DocutilsInlineNode, DocutilsBodyNode,
                   DocutilsGroupingNode, DocutilsDummyNode)
from ..rst import nodes as rst


__all__ = ['Compact_Paragraph', 'Centered', 'HList', 'Index', 'Pending_XRef',
           'Literal_Emphasis', 'Abbreviation', 'Download_Reference', 'SeeAlso',
           'Glossary', 'Start_of_File', 'Todo_Node', 'HighlightLang',
           'Literal_Strong', 'ProductionList', 'Production', 'TermSep', 'Desc',
           'Desc_Signature', 'Desc_Signature_Line', 'Desc_Name',
           'Desc_AddName', 'Desc_Type', 'Desc_ParameterList', 'Desc_Parameter',
           'Desc_Optional', 'Desc_Annotation', 'Desc_Content', 'Desc_Returns',
           'VersionModified', 'Tabular_Col_Spec', 'AutoSummary_Table',
           'Autosummary_ToC', 'Number_Reference']


# other paragraph-level nodes

class Compact_Paragraph(DocutilsGroupingNode):
    pass


class Centered(DocutilsBodyNode):
    def build_flowable(self):
        return Paragraph(super().process_content(), style='centered')


class HList(DocutilsBodyNode):
    def build_flowable(self):
        list = List([list_item.flowable()
                     for hlistcol in self.hlistcol
                     for bullet_list in hlistcol.getchildren()
                     for list_item in bullet_list.getchildren()],
                    style='bulleted')
        list.compact = True
        list.columns = sum(1 for _ in self.hlistcol)
        return list


class HListCol(DocutilsNode):
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


class Inline(rst.Inline):
    class_styles = dict(guilabel='UI control',
                        accelerator='accelerator')


class Literal(rst.Literal):
    class_styles = dict(file='file path',
                        kbd='keystrokes',
                        menuselection='menu cascade',
                        regexp='regular expression',
                        samp='code with variable')


class Literal_Emphasis(rst.Literal):
    style = 'literal emphasis'
    class_styles = dict(mailheader='mail header',
                        mimetype='MIME type',
                        newsgroup='newsgroup')


class Literal_Strong(rst.Literal):
    style = 'literal strong'
    class_styles = dict(command='command',
                        makevar='make variable',
                        program='program')


class ManPage(rst.Inline):
    style = 'man page'


lexers = dict(
    none = TextLexer(stripnl=False),
    python = PythonLexer(stripnl=False),
    python3 = Python3Lexer(stripnl=False),
    pycon = PythonConsoleLexer(stripnl=False),
    pycon3 = PythonConsoleLexer(python3=True, stripnl=False),
    rest = RstLexer(stripnl=False),
    c = CLexer(stripnl=False),
)  # type: Dict[unicode, Lexer]
for _lexer in lexers.values():
    _lexer.add_filter('raiseonerror')


class Literal_Block(rst.Literal_Block):
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
        term = self.process_content()
        kwargs = (dict(definition=self.get('explanation'))
                  if 'explanation' in self.attributes else {})
        return GlossaryTerm(term, style='abbreviation', **kwargs)


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

class SeeAlso(rst.Admonition):
    pass


class VersionModified(DocutilsGroupingNode):
    pass


# special nodes

class Glossary(DocutilsGroupingNode):
    style = 'glossary'


class Start_of_File(DocutilsGroupingNode):
    def build_flowable(self, **kwargs):
        return super().build_flowable(id='%' + self.get('docname'), **kwargs)


class Todo_Node(rst.Admonition):
    pass


class HighlightLang(DocutilsDummyNode):  # these are handled by RinohBuilder
    pass


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
        return DefinitionList(items, style='production list')


class Production(DocutilsBodyNode):
    def build_flowable(self):
        return Paragraph(self.get('tokenname'), style='token')


class TermSep(DocutilsInlineNode):
    def build_styled_text(self):
        return SingleStyledText(', ', style='term separator')


# domain-specific object descriptions

class Desc(DocutilsBodyNode):
    def build_flowable(self):
        term = StaticGroupedFlowables((sig.flowable()
                                       for sig in self.desc_signature),
                                      style='signatures')
        description = self.desc_content.flowable()
        return LabeledFlowable(term, description, style='object description')


class Desc_Signature(DocutilsBodyNode):
    def build_flowable(self):
        if self.get('is_multiline', False):
            lines = (line.styled_text() for line in self.desc_signature_line)
            content = intersperse(lines, '\n')
        else:
            content = self.process_content()
        return Paragraph(content)


class Desc_Signature_Line(DocutilsInlineNode):
    pass


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
    style = 'content'


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


class Autosummary_ToC(DocutilsGroupingNode):
    style = 'autosummary'


class Number_Reference(DocutilsInlineNode):
    def build_styled_text(self):
        return Reference(self.get('refid'), 'reference', style='link')


class Footnotes_Rubric(DocutilsDummyNode):
    """A custom rinohtype-specific node that allows easily excluding footnote
    rubrics from the output"""
