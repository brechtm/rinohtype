# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

try:
    from pygments import lex
    from pygments.filters import ErrorToken
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.lexers.agile import PythonLexer
    from pygments.style import StyleMeta
    from pygments.styles import get_style_by_name
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

from sphinx.highlighting import lexers

from .color import HexColor
from .font.style import BOLD, ITALIC
from .paragraph import Paragraph, ParagraphStyle
from .style import StyledMatcher, StyleSheet, OverrideDefault
from .text import SingleStyledText, TextStyle
from .warnings import warn


__all__ = ['CodeBlock', 'CodeBlockStyle', 'Token',
           'pygments_style_to_stylesheet']


class CodeBlockStyle(ParagraphStyle):
    hyphenate = OverrideDefault(False)
    ligatures = OverrideDefault(False)


class CodeBlock(Paragraph):
    """Paragraph with syntax highlighting"""

    style_class = CodeBlockStyle
    significant_whitespace = True

    def __init__(self, text, language=None, id=None, style=None, parent=None):
        if PYGMENTS_AVAILABLE and language:
            text = self.highlight_block(language, text)
        else:
            warn("The 'pygments' package is not available; cannot perform "
                 "syntax highlighting of {}s.".format(type(self).__name__))
        super().__init__(text, id=id, style=style, parent=parent)

    def highlight_block(self, lang, text):
        # This is a copy of Sphinx's PygmentsBridge.highlight_block() that
        # outputs a list of :class:`Token`\ s instead of marked up text
        if lang in ('py3', 'python3', 'default'):
            if lang in ('py', 'python'):
                if text.startswith('>>>'):
                    # interactive session
                    lexer = lexers['pycon']
                else:
                    lexer = lexers['python']
            elif lang in ('py3', 'python3', 'default'):
                if text.startswith('>>>'):
                    lexer = lexers['pycon3']
                else:
                    lexer = lexers['python3']
            elif lang == 'guess':
                try:
                    lexer = guess_lexer(text)
                except Exception:
                    lexer = lexers['none']
            else:
                if lang in lexers:
                    lexer = lexers[lang]
                else:
                    try:
                        lexer = lexers[lang] = get_lexer_by_name(lang)
                    except ClassNotFound:
                        if warn:
                            warn('Pygments lexer name %r is not known'
                                 % lang)
                            lexer = lexers['none']
                        else:
                            raise
                    else:
                        lexer.add_filter('raiseonerror')
        else:
            lexer = get_lexer_by_name(lang)
        lexer.add_filter('tokenmerge')
        try:
            text = [Token(value, token_type)
                    for token_type, value in lex(text, lexer)]
        except ErrorToken as exc:
            # this is most probably not the selected language,
            # so let it pass unhighlighted
            if lang == 'default':
                pass  # automatic highlighting failed.
            elif warn:
                warn('Could not lex literal_block as "%s". '
                     'Highlighting skipped.' % lang)
            else:
                raise exc
        return text


class Token(SingleStyledText):
    def __init__(self, text, type, style=None, parent=None):
        super().__init__(text, style=style, parent=parent)
        self.type = type

    def __repr__(self):
        """Return a representation of this single-styled text; the text string
        along with a representation of its :class:`TextStyle`."""
        return "{0}('{1}', type={2})".format(self.__class__.__name__,
                                              self.text(None), self.type)

    def _short_repr_kwargs(self, flowable_target):
        yield 'type={}'.format(self.type)
        for kwarg in super()._short_repr_kwargs(flowable_target):
            yield kwarg


def get_pygments_style(style):
    """Retrieve a Pygments style by name, by import path or, if `style` is
    already Pygments style, simply return it."""
    if isinstance(style, StyleMeta):
        return style
    if '.' in style:  # by python package/module
        module, name = style.rsplit('.', 1)
        return getattr(__import__(module, None, None, ['__name__']), name)
    else:             # by name
        if style == 'sphinx':
            from sphinx.pygments_styles import SphinxStyle
            return SphinxStyle
        elif style == 'pyramid':
            from sphinx.pygments_styles import PyramidStyle
            return PyramidStyle
        elif style == 'none':
            from sphinx.pygments_styles import NoneStyle
            return NoneStyle
        else:
            return get_style_by_name(style)


def pygments_style_to_stylesheet(style):
    if not PYGMENTS_AVAILABLE:
        return None
    pygments_style = get_pygments_style(style)
    matcher = StyledMatcher()
    style_sheet_name = '{} (pygments)'.format(pygments_style.__name__)
    style_sheet = StyleSheet(style_sheet_name, matcher=matcher)
    for token_type, style in pygments_style:
        style_name = '(pygments){}'.format(token_type)
        matcher[style_name] = Token.like(type=token_type)
        style_attributes = {}
        if style['italic']:
            style_attributes['font_slant'] = ITALIC
        if style['bold']:
            style_attributes['font_weight'] = BOLD
        if style['color']:
            style_attributes['font_color'] = HexColor(style['color'])
        # TODO: underline, bgcolor, border, roman, sans, mono
        style_sheet[style_name] = TextStyle(**style_attributes)
    return style_sheet
