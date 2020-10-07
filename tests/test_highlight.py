# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

try:
    import pygments
    from pygments.style import Style
    from pygments.token import (Comment, Keyword, Number, Text, Name,
                                Punctuation,
                                Operator, Literal, is_token_subtype)

    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False


try:
    import sphinx
    HAS_SPHINX = True
except ImportError:
    HAS_SPHINX = False


from rinoh.color import HexColor
from rinoh.font import FontSlant, FontWeight
from rinoh.highlight import (highlight_block, get_pygments_style, Token,
                             pygments_style_to_stylesheet)


requires_pygments = pytest.mark.skipif(not HAS_PYGMENTS,
                                       reason='Pygments is not available')
requires_sphinx = pytest.mark.skipif(not HAS_SPHINX,
                                     reason='Sphinx is not available')


@requires_pygments
def test_highlight_block():
    code = ("""def sandwich(bread, cheese=True):
                   result = []
                   result.append(bread.slice())
                   if cheese:
                       result.append('cheese')
                   return result""")
    indent = 15 * ' '
    result = highlight_block('python', code, None)
    reference = \
        [Token('def', Keyword), Token(' ', Text),
           Token('sandwich', Name.Function), Token('(', Punctuation),
           Token('bread', Name), Token(',', Punctuation), Token(' ', Text),
           Token('cheese', Name), Token('=', Operator),
           Token('True', Keyword.Constant), Token('):', Punctuation),
         Token('\n' + indent + '    ', Text), Token('result', Name),
           Token(' ', Text), Token('=', Operator), Token(' ', Text),
           Token('[]', Punctuation),
         Token('\n' + indent + '    ', Text), Token('result', Name),
           Token('.', Operator), Token('append', Name), Token('(', Punctuation),
           Token('bread', Name), Token('.', Operator), Token('slice', Name),
           Token('())', Punctuation),
         Token('\n' + indent + '    ', Text), Token('if', Keyword),
           Token(' ', Text), Token('cheese', Name), Token(':', Punctuation),
         Token('\n' + indent + '    ' + '    ', Text), Token('result', Name),
           Token('.', Operator), Token('append', Name), Token('(', Punctuation),
           Token("'cheese'", Literal.String), Token(')', Punctuation),
         Token('\n' + indent + '    ', Text), Token('return', Keyword),
           Token(' ', Text), Token('result', Name), Token('\n', Text)]
    for res, ref in zip(result, reference):
        assert res.text(None) == ref.text(None)
        assert is_token_subtype(res.type, ref.type)


@requires_pygments
def test_get_pygments_style():
    assert get_pygments_style('default') == pygments.styles.default.DefaultStyle
    assert get_pygments_style('monokai') == pygments.styles.monokai.MonokaiStyle
    assert get_pygments_style('borland') == pygments.styles.borland.BorlandStyle
    assert get_pygments_style('fruity') == pygments.styles.fruity.FruityStyle
    assert get_pygments_style('tango') == pygments.styles.tango.TangoStyle
    assert get_pygments_style('vim') == pygments.styles.vim.VimStyle
    assert (get_pygments_style('pygments.styles.colorful.ColorfulStyle')
            == pygments.styles.colorful.ColorfulStyle)
    assert (get_pygments_style('pygments.styles.vs.VisualStudioStyle')
            == pygments.styles.vs.VisualStudioStyle)


@requires_sphinx
def test_get_pygments_style_sphinx():
    assert get_pygments_style('none') == sphinx.pygments_styles.NoneStyle
    assert get_pygments_style('sphinx') == sphinx.pygments_styles.SphinxStyle
    assert get_pygments_style('pyramid') == sphinx.pygments_styles.PyramidStyle
    assert (get_pygments_style('sphinx.pygments_styles.SphinxStyle')
                == sphinx.pygments_styles.SphinxStyle)
    assert (get_pygments_style(sphinx.pygments_styles.SphinxStyle)
                == sphinx.pygments_styles.SphinxStyle)


@requires_pygments
def test_pygments_style_to_stylesheet():
    def matching_style(style_sheet, token_type):
        token = Token('text', token_type)
        match, = style_sheet.find_matches(token, None)
        return style_sheet[match.style_name]

    class SimpleStyle(Style):
        background_color = "#f0f0f0"
        default_style = ""

        styles = {
            Comment: "italic #60a0b0",
            Keyword: "bold #007020",
            Number:  "#40a070",
        }

    style_sheet = pygments_style_to_stylesheet(SimpleStyle)

    comment_style = matching_style(style_sheet, Comment)
    assert comment_style.keys() == set(['font_slant', 'font_color'])
    assert comment_style.font_slant == FontSlant.ITALIC
    assert comment_style.font_color == HexColor('#60a0b0')

    keyword_style = matching_style(style_sheet, Keyword)
    assert keyword_style.keys() == set(['font_weight', 'font_color'])
    assert keyword_style.font_weight == FontWeight.BOLD
    assert keyword_style.font_color == HexColor('#007020')

    number_style = matching_style(style_sheet, Number)
    assert number_style.keys() == set(['font_color'])
    assert number_style.font_color == HexColor('#40a070')

    for token in (Text, Name, Punctuation, Operator, Literal, Name.Builtin,
                  Name.Builtin.Pseudo, Literal.String):
        style = matching_style(style_sheet, token)
        assert not style.keys()
