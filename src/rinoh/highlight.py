# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

try:
    from pygments import lex
    from pygments.filters import ErrorToken
    from pygments.lexers import get_lexer_by_name
    from pygments.style import StyleMeta
    from pygments.styles import get_style_by_name
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

from .attribute import OverrideDefault
from .color import HexColor
from .font.style import BOLD, ITALIC
from .paragraph import Paragraph, ParagraphStyle
from .style import StyledMatcher, StyleSheet
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

    def __init__(self, text, language=None, id=None, style=None, parent=None,
                 lexer_getter=None):
        if PYGMENTS_AVAILABLE:
            text = highlight_block(language or 'text', text, lexer_getter)
        else:
            warn("The 'pygments' package is not available; cannot perform "
                 "syntax highlighting of {}s.".format(type(self).__name__))
        super().__init__(text, id=id, style=style, parent=parent)


def highlight_block(language, text, lexer_getter):
    get_lexer = lexer_getter or (lambda text, lang: get_lexer_by_name(lang))
    lexer = get_lexer(text, language)
    lexer.add_filter('tokenmerge')
    try:
        text = [Token(value, token_type)
                for token_type, value in lex(text, lexer)]
    except ErrorToken as exc:
        # this is most probably not the selected language,
        # so let it pass unhighlighted
        if language == 'default':
            pass  # automatic highlighting failed.
        elif warn:
            warn('Could not lex literal_block as "%s". '
                 'Highlighting skipped.' % language)
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


def pygments_style_to_stylesheet(style, base=None):
    if not PYGMENTS_AVAILABLE:
        return None
    pygments_style = get_pygments_style(style)
    matcher = StyledMatcher()
    style_sheet_name = '{} (pygments)'.format(pygments_style.__name__)
    style_sheet = StyleSheet(style_sheet_name, matcher=matcher, base=base)
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
