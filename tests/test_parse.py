
import pytest

from rinoh.attribute import OptionSet, Bool, Integer
from rinoh.color import Color, HexColor
from rinoh.dimension import DimensionBase, PT, PICA, INCH, MM, CM, PERCENT
from rinoh.draw import Stroke
from rinoh.number import (NumberFormat, NUMBER, CHARACTER_LC, CHARACTER_UC,
                          ROMAN_LC, ROMAN_UC, SYMBOL)
from rinoh.flowable import HorizontalAlignment, LEFT, RIGHT, CENTER, Break, ANY
from rinoh.paragraph import (TextAlign, JUSTIFY, TabAlign,
                             LineSpacing, DEFAULT, STANDARD, SINGLE, DOUBLE,
                             ProportionalSpacing, FixedSpacing, Leading)
from rinoh.reference import ReferenceField, TITLE, PAGE, ReferenceText
from rinoh.style import (parse_keyword, parse_string, parse_number,
                         parse_selector_args, StyleParseError, CharIterator)
from rinoh.table import VerticalAlign, TOP, MIDDLE, BOTTOM
from rinoh.text import StyledText, SingleStyledText, MixedStyledText, Tab


def test_optionset_from_string():
    ONE = 'one'
    TWO = 'two'
    THREE = 'three'

    class TestSet1(OptionSet):
        values = ONE, TWO, THREE

    assert TestSet1.from_string('one') == ONE
    assert TestSet1.from_string('TWO') == TWO
    assert TestSet1.from_string('tHRee') == THREE
    with pytest.raises(ValueError):
        TestSet1.from_string('four')
    with pytest.raises(ValueError):
        TestSet1.from_string('none')


    class TestSet2(OptionSet):
        values = None, TWO

    assert TestSet2.from_string('none') == None
    assert TestSet2.from_string('nONe') == None
    assert TestSet2.from_string('two') == TWO
    with pytest.raises(ValueError):
        TestSet2.from_string('one')
    with pytest.raises(ValueError):
        TestSet2.from_string('False')


def test_numberformat_from_string():
    assert NumberFormat.from_string('none') == None
    assert NumberFormat.from_string('number') == NUMBER
    assert NumberFormat.from_string('lowercase character') == CHARACTER_LC
    assert NumberFormat.from_string('uppercase CHARACTER') == CHARACTER_UC
    assert NumberFormat.from_string('LOWERCASE ROMAN') == ROMAN_LC
    assert NumberFormat.from_string('uppercase roman') == ROMAN_UC
    assert NumberFormat.from_string('sYMBOl') == SYMBOL
    with pytest.raises(ValueError):
        NumberFormat.from_string('Character')
    with pytest.raises(ValueError):
        NumberFormat.from_string('roMAN')


def test_textalign_from_string():
    assert TextAlign.from_string('left') == LEFT
    assert TextAlign.from_string('cenTER') == CENTER
    assert TextAlign.from_string('RighT') == RIGHT
    assert TextAlign.from_string('justify') == JUSTIFY
    with pytest.raises(ValueError):
        assert TextAlign.from_string('none')
    with pytest.raises(ValueError):
        assert TextAlign.from_string('full')


def test_horizontalalignment_from_string():
    assert HorizontalAlignment.from_string('left') == LEFT
    assert HorizontalAlignment.from_string('Right') == RIGHT
    assert HorizontalAlignment.from_string('CENTER') == CENTER
    with pytest.raises(ValueError):
        HorizontalAlignment.from_string('none')


def test_break_from_string():
    assert Break.from_string('none') == None
    assert Break.from_string('aNY') == ANY
    with pytest.raises(ValueError):
        assert Break.from_string('center')


def test_tabalign_from_string():
    assert TabAlign.from_string('left') == LEFT
    assert TabAlign.from_string('right') == RIGHT
    assert TabAlign.from_string('center') == CENTER
    with pytest.raises(ValueError):
        assert TabAlign.from_string('none')
    with pytest.raises(ValueError):
        assert TabAlign.from_string('any')


def test_linespacing_from_string():
    assert LineSpacing.from_string('default') == DEFAULT
    assert LineSpacing.from_string('StandarD') == STANDARD
    assert LineSpacing.from_string('SINGLE') == SINGLE
    assert LineSpacing.from_string('Double') == DOUBLE
    assert LineSpacing.from_string('proportional(2)') == ProportionalSpacing(2)
    assert LineSpacing.from_string('fixed(2pt)') == FixedSpacing(2*PT)
    assert LineSpacing.from_string('fixed(1.4 cm)') == FixedSpacing(1.4*CM)
    assert LineSpacing.from_string('fixed(1pT,single)') == FixedSpacing(1*PT)
    assert LineSpacing.from_string('fixed(1pT ,DOUBLE)') == FixedSpacing(1*PT,
                                                                         DOUBLE)
    assert LineSpacing.from_string('leading(3    PT)') == Leading(3*PT)
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('5 pt')
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('proportional')
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('proportional(1 cm)')
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('fixed')
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('fixed(2)')
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('fixed(2pt, badvalue)')
    with pytest.raises(ValueError):
        assert LineSpacing.from_string('leading')


def test_verticalalign_from_string():
    assert VerticalAlign.from_string('top') == TOP
    assert VerticalAlign.from_string('miDDLE') == MIDDLE
    assert VerticalAlign.from_string('BOTTOM') == BOTTOM
    with pytest.raises(ValueError):
        assert VerticalAlign.from_string('none')
    with pytest.raises(ValueError):
        assert VerticalAlign.from_string('center')


def test_bool_from_string():
    assert Bool.from_string('true') == True
    assert Bool.from_string('false') == False
    assert Bool.from_string('TRUE') == True
    assert Bool.from_string('FALSE') == False
    assert Bool.from_string('True') == True
    assert Bool.from_string('FaLSE') == False
    with pytest.raises(ValueError):
        Bool.from_string('1')
    with pytest.raises(ValueError):
        Bool.from_string('0')
    with pytest.raises(ValueError):
        Bool.from_string('T')
    with pytest.raises(ValueError):
        Bool.from_string('f')


def test_integer_from_string():
    assert Integer.from_string('1') == 1
    assert Integer.from_string('001') == 1
    assert Integer.from_string('873654354') == 873654354
    assert Integer.from_string('-9') == -9
    with pytest.raises(ValueError):
        assert Integer.from_string('1e5')
    with pytest.raises(ValueError):
        assert Integer.from_string('0.5')


def test_dimensionbase_from_string():
    assert DimensionBase.from_string('none') == None
    assert DimensionBase.from_string('0') == 0
    assert DimensionBase.from_string('1pt') == 1*PT
    assert DimensionBase.from_string('10 pt') == 10*PT
    assert DimensionBase.from_string('25pc') == 25*PICA
    assert DimensionBase.from_string('1.5 in') == 1.5*INCH
    assert DimensionBase.from_string('99999mm') == 99999*MM
    assert DimensionBase.from_string('-2.1 cm') == -2.1*CM
    assert DimensionBase.from_string('21%') == 21.00*PERCENT
    assert DimensionBase.from_string('-16.12%') == -16.12*PERCENT
    with pytest.raises(ValueError):
        assert DimensionBase.from_string('20inch')


def test_color_from_string():
    assert Color.from_string('none') == None
    assert Color.from_string('#ffffff') == HexColor('#FFFFFF')
    assert Color.from_string('#aBc123') == HexColor('#Abc123')
    assert Color.from_string('#123456aa') == HexColor('#123456aa')
    assert Color.from_string('#5e1') == HexColor('#5e1')
    assert Color.from_string('#5e10') == HexColor('#5e10')


def test_stroke_from_string():
    assert Stroke.from_string('1pt,#fff') == Stroke(1*PT, HexColor('#FFF'))
    assert Stroke.from_string('99cm,#123456aa') == Stroke(99*CM,
                                                         HexColor('#123456aa'))
    with pytest.raises(ValueError):
        assert Stroke.from_string('8,#fff')
    with pytest.raises(ValueError):
        assert Stroke.from_string('1pt,1')
    with pytest.raises(ValueError):
        assert Stroke.from_string('xyz')


def test_styledtext_from_string():
    assert StyledText.from_string("'one'") \
           == MixedStyledText([SingleStyledText('one')])
    assert StyledText.from_string("'on\\'e'") \
           == MixedStyledText([SingleStyledText("on'e")])
    assert StyledText.from_string("'one' 'two'") \
           == MixedStyledText([SingleStyledText('one'),
                               SingleStyledText('two')])
    assert StyledText.from_string("'one'(style1)") \
           == MixedStyledText([SingleStyledText('one', style='style1')])
    assert StyledText.from_string("'one' (style1)") \
           == MixedStyledText([SingleStyledText('one', style='style1')])
    assert StyledText.from_string("'one'(style1) 'two'") \
           == MixedStyledText([SingleStyledText('one', style='style1'),
                               SingleStyledText('two')])
    assert StyledText.from_string("'one'\t(style1) 'two'(style2)") \
           == MixedStyledText([SingleStyledText('one', style='style1'),
                               SingleStyledText('two', style='style2')])
    assert StyledText.from_string("'one{nbsp}two'") \
           == MixedStyledText([SingleStyledText('one\N{NO-BREAK SPACE}two')])
    assert StyledText.from_string("'one' '{gt}two'(style2)") \
           == MixedStyledText([SingleStyledText('one'),
                               SingleStyledText('>two', style='style2')])


def test_referencetext_from_string():
    assert ReferenceText.from_string("'Chapter {NUMBER}\t{title}'") \
           == MixedStyledText(
                  [MixedStyledText([SingleStyledText('Chapter '),
                                    ReferenceField(NUMBER), Tab(),
                                    ReferenceField(TITLE)])])
    assert ReferenceText.from_string("'{bull} '(style1)"
                                     "'{nbsp}{TITLE}\t{PaGE}'(style2)") \
           == MixedStyledText(
                  [MixedStyledText([SingleStyledText('\N{BULLET} ')],
                                   style='style1'),
                   MixedStyledText([SingleStyledText('\N{NO-BREAK SPACE}'),
                                    ReferenceField(TITLE), Tab(),
                                    ReferenceField(PAGE)],
                                   style='style2')])


# selectors

def test_parse_keyword():
    def helper(string):
        chars = iter(string)
        return parse_keyword(chars), ''.join(chars)

    assert helper('style=') == ('style', '')
    assert helper('row =') == ('row', '')
    assert helper('UPPERCASE=') == ('UPPERCASE', '')
    assert helper('miXeDCaSE=') == ('miXeDCaSE', '')
    assert helper('key =  efzef') == ('key', '  efzef')
    with pytest.raises(StyleParseError):
        helper('bad key =')


def test_parse_string():
    def helper(string):
        chars = iter(string)
        return parse_string(next(chars), chars), ''.join(chars)

    assert helper('"test"') == ('test', '')
    assert helper("'test'") == ('test', '')
    assert helper("'test' trailing text") == ('test', ' trailing text')
    assert helper("'A string with spaces'") == ('A string with spaces', '')
    assert helper("""'Quotes ahead: " '""") == ('Quotes ahead: " ', '')
    assert helper(r"'Escaped quote: \' '") == ("Escaped quote: ' ", '')
    assert helper(r"'Unicode \N{COLON} lookup'") == ('Unicode : lookup', '')


def test_parse_number():
    def helper(string):
        chars = CharIterator(string)
        return parse_number(next(chars), chars), ''.join(chars)

    assert helper('1') == (1, '')
    assert helper('+1') == (1, '')
    assert helper('-1') == (-1, '')
    assert helper('12497   ') == (12497, '   ')
    assert helper('1.05') == (1.05, '')
    assert helper('-1.05') == (-1.05, '')
    assert helper('+1.05') == (1.05, '')
    assert helper('0.2478  zzz ') == (0.2478, '  zzz ')
    assert helper('1.45e10') == (1.45e10, '')
    assert helper('1.45e+10') == (1.45e+10, '')
    assert helper('1.45e-10') == (1.45e-10, '')


def test_parse_selector_args():
    assert parse_selector_args("'style name'") == (['style name'], {})
    assert parse_selector_args("666") == ([666], {})
    assert parse_selector_args("'style name', 666") == (['style name', 666], {})
    assert parse_selector_args("'style name' ,666") == (['style name', 666], {})
    assert parse_selector_args("'style name',666") == (['style name', 666], {})
    assert parse_selector_args("'arg1', 'arg2'") == (['arg1', 'arg2'], {})
    assert parse_selector_args("key='value'") == ([], dict(key='value'))
    assert parse_selector_args("key=123") == ([], dict(key=123))
    assert parse_selector_args("k1=13,k2='meh'") == ([], dict(k1=13, k2='meh'))
    assert parse_selector_args("key9='value'") == ([], dict(key9='value'))
    assert parse_selector_args("key_9='value'") == ([], dict(key_9='value'))
    assert parse_selector_args("'arg', key='value'") == (['arg'],
                                                          dict(key='value'))
    assert parse_selector_args("22, key='value'") == ([22], dict(key='value'))
