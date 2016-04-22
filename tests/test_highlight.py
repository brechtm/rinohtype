
import pytest

from pygments.lexers.agile import PythonLexer
from pygments.style import Style
from pygments.token import (Comment, Keyword, Number, Text, Name, Punctuation,
                            Operator, Literal)

from rinoh.color import HexColor
from rinoh.font import ITALIC
from rinoh.font.style import BOLD
from rinoh.highlight import highlight, pygments_style_to_stylesheet, Token


def test_highlight():
    code = ("""def sandwich(bread, cheese=True):
                   result = []
                   result.append(bread.slice())
                   if cheese:
                       result.append('cheese')
                   return result""")
    indent = 15 * ' '
    assert list(highlight(code, PythonLexer())) == \
        [Token('def', Keyword), Token(' ', Text),
           Token('sandwich', Name.Function), Token('(', Punctuation),
           Token('bread', Name), Token(',', Punctuation), Token(' ', Text),
           Token('cheese', Name), Token('=', Operator),
           Token('True', Name.Builtin.Pseudo), Token('):', Punctuation),
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


def test_pygments_style_to_stylesheet():
    def matching_style(style_sheet, token_type):
        match, = style_sheet.find_matches(Token('text', token_type), None)
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
    assert comment_style.font_slant == ITALIC
    assert comment_style.font_color == HexColor('#60a0b0')

    keyword_style = matching_style(style_sheet, Keyword)
    assert keyword_style.keys() == set(['font_weight', 'font_color'])
    assert keyword_style.font_weight == BOLD
    assert keyword_style.font_color == HexColor('#007020')

    number_style = matching_style(style_sheet, Number)
    assert number_style.keys() == set(['font_color'])
    assert number_style.font_color == HexColor('#40a070')

    for token in (Text, Name, Punctuation, Operator, Literal, Name.Builtin,
                  Name.Builtin.Pseudo, Literal.String):
        style = matching_style(style_sheet, token)
        assert not style.keys()
