
import pytest

from rinoh.attribute import OptionSet, Bool, Integer
from rinoh.color import Color, HexColor
from rinoh.dimension import (Dimension, PT, PICA, INCH, MM, CM,
                             PERCENT, QUARTERS)
from rinoh.draw import Stroke
from rinoh.flowable import HorizontalAlignment, Break
from rinoh.image import BackgroundImage, Scale
from rinoh.number import NumberFormat
from rinoh.paper import Paper, A4, A5, JUNIOR_LEGAL
from rinoh.paragraph import (Paragraph, TextAlign, TabAlign,
                             LineSpacing, DEFAULT, STANDARD, SINGLE, DOUBLE,
                             ProportionalSpacing, FixedSpacing, Leading)
from rinoh.reference import (ReferenceField, ReferenceText, Field, PAGE_NUMBER,
                             NUMBER_OF_PAGES, SECTION_TITLE, SECTION_NUMBER)
from rinoh.strings import StringField
from rinoh.structure import SectionTitles, AdmonitionTitles
from rinoh.style import (SelectorByName, parse_selector, parse_selector_args,
                         parse_class_selector, parse_keyword, parse_string,
                         parse_number, StyleParseError, CharIterator)
from rinoh.table import VerticalAlign
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
    assert NumberFormat.from_string('number') == NumberFormat.NUMBER
    assert NumberFormat.from_string('lowercase character') \
               == NumberFormat.LOWERCASE_CHARACTER
    assert NumberFormat.from_string('uppercase CHARACTER') \
               == NumberFormat.UPPERCASE_CHARACTER
    assert NumberFormat.from_string('LOWERCASE ROMAN') \
               == NumberFormat.LOWERCASE_ROMAN
    assert NumberFormat.from_string('uppercase roman') \
               == NumberFormat.UPPERCASE_ROMAN
    assert NumberFormat.from_string('sYMBOl') == NumberFormat.SYMBOL
    with pytest.raises(ValueError):
        NumberFormat.from_string('Character')
    with pytest.raises(ValueError):
        NumberFormat.from_string('roMAN')


def test_textalign_from_string():
    assert TextAlign.from_string('left') == TextAlign.LEFT
    assert TextAlign.from_string('cenTER') == TextAlign.CENTER
    assert TextAlign.from_string('RighT') == TextAlign.RIGHT
    assert TextAlign.from_string('justify') == TextAlign.JUSTIFY
    with pytest.raises(ValueError):
        assert TextAlign.from_string('none')
    with pytest.raises(ValueError):
        assert TextAlign.from_string('full')


def test_horizontalalignment_from_string():
    assert HorizontalAlignment.from_string('left') == HorizontalAlignment.LEFT
    assert HorizontalAlignment.from_string('Right') \
               == HorizontalAlignment.RIGHT
    assert HorizontalAlignment.from_string('CENTER') \
               == HorizontalAlignment.CENTER
    with pytest.raises(ValueError):
        HorizontalAlignment.from_string('none')


def test_break_from_string():
    assert Break.from_string('none') == None
    assert Break.from_string('Left') == Break.LEFT
    assert Break.from_string('RIGHT') == Break.RIGHT
    assert Break.from_string('aNY') == Break.ANY
    with pytest.raises(ValueError):
        assert Break.from_string('center')


def test_tabalign_from_string():
    assert TabAlign.from_string('left') == TabAlign.LEFT
    assert TabAlign.from_string('right') == TabAlign.RIGHT
    assert TabAlign.from_string('center') == TabAlign.CENTER
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
    assert LineSpacing.from_string('fixed(1pT ,DOUBLE)') \
               == FixedSpacing(1*PT, DOUBLE)
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
    assert VerticalAlign.from_string('top') == VerticalAlign.TOP
    assert VerticalAlign.from_string('miDDLE') == VerticalAlign.MIDDLE
    assert VerticalAlign.from_string('BOTTOM') == VerticalAlign.BOTTOM
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


def test_dimension_from_string():
    assert Dimension.from_string('none') == None
    assert Dimension.from_string('0') == 0
    assert Dimension.from_string('1pt') == 1*PT
    assert Dimension.from_string('10 pt') == 10*PT
    assert Dimension.from_string('25pc') == 25*PICA
    assert Dimension.from_string('1.5 in') == 1.5*INCH
    assert Dimension.from_string('99999mm') == 99999*MM
    assert Dimension.from_string('-2.1 cm') == -2.1*CM
    assert Dimension.from_string('21%') == 21*PERCENT
    assert Dimension.from_string('-16.12%') == -16.12*PERCENT
    assert Dimension.from_string('3/4') == 3*QUARTERS
    with pytest.raises(ValueError):
        assert Dimension.from_string('20inch')


def test_paper_from_string():
    assert Paper.from_string('A4') == A4
    assert Paper.from_string('a5') == A5
    assert Paper.from_string('junIOr legal') == JUNIOR_LEGAL
    assert Paper.from_string('212pt * 5.84in') == Paper('212pt * 5.84in',
                                                         212*PT, 5.84*INCH)
    assert Paper.from_string('2 cm * 4cm') == Paper('2 cm * 4cm', 2*CM, 4*CM)
    assert Paper.from_string('2cm * 4 cm') == Paper('2cm * 4 cm', 2*CM, 4*CM)
    assert Paper.from_string('2cm*4cm') == Paper('2cm*4cm', 2*CM, 4*CM)
    assert Paper.from_string('2  cm*4  cm') == Paper('2  cm*4  cm', 2*CM, 4*CM)
    with pytest.raises(ValueError):
        Paper.from_string('212pt * 5.84in * 6cm')
    with pytest.raises(ValueError):
        Paper.from_string('212pt * 5.84')


def test_color_from_string():
    assert Color.from_string('none') == None
    assert Color.from_string('#ffffff') == HexColor('#FFFFFF')
    assert Color.from_string('#aBc123') == HexColor('#Abc123')
    assert Color.from_string('#123456aa') == HexColor('#123456aa')
    assert Color.from_string('#5e1') == HexColor('#5e1')
    assert Color.from_string('#5e10') == HexColor('#5e10')


def test_stroke_from_string():
    assert Stroke.from_string('1pt,#fff') == Stroke(1*PT, HexColor('#FFF'))
    assert Stroke.from_string('1pt, #fff') == Stroke(1*PT, HexColor('#FFF'))
    assert Stroke.from_string('99cm,#123456aa') == Stroke(99*CM,
                                                         HexColor('#123456aa'))
    with pytest.raises(ValueError):
        assert Stroke.from_string('8,#fff')
    with pytest.raises(ValueError):
        assert Stroke.from_string('1pt,1')
    with pytest.raises(ValueError):
        assert Stroke.from_string('xyz')


def test_styledtext_from_string():
    assert StyledText.from_string("'one'") == SingleStyledText('one')
    assert StyledText.from_string("'on\\'e'") == SingleStyledText("on'e")
    assert StyledText.from_string("'one' 'two'") \
           == MixedStyledText([SingleStyledText('one'),
                               SingleStyledText('two')])
    assert StyledText.from_string("'one'(style1)") \
           == SingleStyledText('one', style='style1')
    assert StyledText.from_string("'one' (style1)") \
           == SingleStyledText('one', style='style1')
    assert StyledText.from_string("'one'(style1) 'two'") \
           == MixedStyledText([SingleStyledText('one', style='style1'),
                               SingleStyledText('two')])
    assert StyledText.from_string("'one'\t(style1) 'two'(style2)") \
           == MixedStyledText([SingleStyledText('one', style='style1'),
                               SingleStyledText('two', style='style2')])
    assert StyledText.from_string("'one{nbsp}two'") \
           == SingleStyledText('one\N{NO-BREAK SPACE}two')
    assert StyledText.from_string("'one' '{gt}two'(style2)") \
           == MixedStyledText([SingleStyledText('one'),
                               SingleStyledText('>two', style='style2')])

    # with fields
    assert StyledText.from_string("'{SECTION_NUMBER(7)}' (style)") \
           == Field(SECTION_NUMBER(7), style='style')
    assert StyledText.from_string("'abc {NUMBER_OF_PAGES}' (style)") \
           == MixedStyledText([SingleStyledText('abc '),
                               Field(NUMBER_OF_PAGES)], style='style')
    assert StyledText.from_string("'{PAGE_NUMBER}abc' (style)") \
           == MixedStyledText([Field(PAGE_NUMBER),
                               SingleStyledText('abc')], style='style')
    assert StyledText.from_string("'one{nbsp}two{SECTION_TITLE(1)}'") \
           == MixedStyledText([SingleStyledText('one\N{NO-BREAK SPACE}two'),
                               Field(SECTION_TITLE(1))])
    assert StyledText.from_string("'one{PAGE_NUMBER}'(style1) 'moh'(style2)") \
           == MixedStyledText([MixedStyledText([SingleStyledText('one'),
                                                Field(PAGE_NUMBER)],
                                               style='style1'),
                               SingleStyledText('moh', style='style2')])
    assert StyledText.from_string("'{SectionTitles.chapter}abc' (style)") \
           == MixedStyledText([StringField(SectionTitles, 'chapter'),
                               SingleStyledText('abc')], style='style')
    assert StyledText.from_string("'1{AdmonitionTitles.warning}2' (style)") \
           == MixedStyledText([SingleStyledText('1'),
                               StringField(AdmonitionTitles, 'warning'),
                               SingleStyledText('2')], style='style')


def test_referencetext_from_string():
    assert ReferenceText.from_string("'{NUMBER}'") == ReferenceField('number')
    assert ReferenceText.from_string("'Chapter {NUMBER}\t{title}'") \
           == MixedStyledText([SingleStyledText('Chapter '),
                               ReferenceField('number'), Tab(),
                               ReferenceField('title')])
    assert ReferenceText.from_string("'{bull} '(style1)"
                                     "'{nbsp}{TITLE}\t{PaGE}'(style2)") \
           == MixedStyledText(
                  [SingleStyledText('\N{BULLET} ', style='style1'),
                   MixedStyledText([SingleStyledText('\N{NO-BREAK SPACE}'),
                                    ReferenceField('title'), Tab(),
                                    ReferenceField('page')],
                                   style='style2')])


def test_scale_from_string():
    assert Scale.from_string("0.1") == 0.1
    assert Scale.from_string("1.0") == 1.0
    assert Scale.from_string("0.5") == 0.5
    assert Scale.from_string("fit") == Scale.FIT
    assert Scale.from_string("fill") == Scale.FILL
    with pytest.raises(ValueError):
        Scale.from_string("unknown")
    with pytest.raises(ValueError):
        Scale.from_string("/")
    with pytest.raises(ValueError):
        Scale.from_string("0")
    with pytest.raises(ValueError):
        assert Scale.from_string("-0.5")


def test_backgroundimage_from_string():
    assert BackgroundImage.from_string("'image.jpg'") \
               == BackgroundImage('image.jpg')
    assert BackgroundImage.from_string("'image.jpg'   ") \
               == BackgroundImage('image.jpg')
    assert BackgroundImage.from_string("'image.jpg' scale=0.6  ") \
               == BackgroundImage('image.jpg', scale=0.6)
    assert BackgroundImage.from_string("'image.jpg' scale=fit  ") \
               == BackgroundImage('image.jpg', scale='fit')
    assert BackgroundImage.from_string("'image.jpg' width=9 cm  ") \
               == BackgroundImage('image.jpg', width=9*CM)
    assert BackgroundImage.from_string("'image.jpg' width=2 cm height=5cm") \
               == BackgroundImage('image.jpg', width=2*CM, height=5*CM)
    assert BackgroundImage.from_string("'image.jpg' scale=fill dpi = 56") \
               == BackgroundImage('image.jpg', scale='fill', dpi=56)
    assert BackgroundImage.from_string("'image.jpg' height=2cm rotate =20 "
                                       "align=   right limit_width = 5cm") \
               == BackgroundImage('image.jpg', height=2*CM, rotate=20,
                                  align='right', limit_width=5*CM)
    with pytest.raises(ValueError):
        BackgroundImage.from_string("'image.jpg'  unsupported_keyword=5")


# selectors

def test_parse_keyword():
    def helper(string):
        chars = CharIterator(string)
        return parse_keyword(chars), ''.join(chars)

    assert helper('style=') == ('style', '')
    assert helper('row =') == ('row', '')
    assert helper('UPPERCASE=') == ('UPPERCASE', '')
    assert helper('miXeDCaSE=') == ('miXeDCaSE', '')
    assert helper('key =  efzef') == ('key', '  efzef')
    with pytest.raises(StyleParseError):
        helper('bad key =')
    with pytest.raises(StyleParseError):
        helper('bad')


def test_parse_string():
    def helper(string):
        chars = iter(string)
        return parse_string(chars), ''.join(chars)

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
        return parse_number(chars), ''.join(chars)

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
    def helper(string):
        chars = CharIterator('({})'.format(string))
        return parse_selector_args(chars)

    assert helper("") == ([], {})
    assert helper("   ") == ([], {})
    assert helper("'style name'") == (['style name'], {})
    assert helper("666") == ([666], {})
    assert helper("'baboo', ") == (['baboo'], {})
    assert helper("22, ") == ([22], {})
    assert helper("'style name', 666") == (['style name', 666], {})
    assert helper("'style name' ,666") == (['style name', 666], {})
    assert helper("'style name',666") == (['style name', 666], {})
    assert helper("'arg1', 'arg2'") == (['arg1', 'arg2'], {})
    assert helper("key='value'") == ([], dict(key='value'))
    assert helper("key=123") == ([], dict(key=123))
    assert helper("k1=13,k2='meh'") == ([], dict(k1=13, k2='meh'))
    assert helper("key9='value'") == ([], dict(key9='value'))
    assert helper("key_9='value'") == ([], dict(key_9='value'))
    assert helper("'arg', key='value'") == (['arg'], dict(key='value'))
    assert helper("22, key='value'") == ([22], dict(key='value'))


def test_parse_class_selector():
    def helper(string):
        chars = CharIterator(string)
        return parse_class_selector(chars), ''.join(chars)

    assert helper('Paragraph') == (Paragraph, '')
    assert helper('Paragraph   ') == (Paragraph, '   ')
    assert helper('  Paragraph') == (Paragraph, '')
    assert helper('  Paragraph ') == (Paragraph, ' ')
    assert helper('Paragraph()') == (Paragraph.like(), '')
    assert helper('Paragraph(   )') == (Paragraph.like(), '')
    assert helper("Paragraph('style')") == (Paragraph.like('style'), '')
    assert helper("Paragraph('style', "
                  "meh=5)") == (Paragraph.like('style', meh=5), '')
    assert helper(" StyledText('style')  ") == (StyledText.like('style'), '  ')


def test_parse_selector():
    assert parse_selector("Paragraph") == Paragraph
    assert parse_selector("Paragraph / StyledText") == Paragraph / StyledText
    assert parse_selector("  Paragraph / StyledText") == Paragraph / StyledText
    assert parse_selector(" Paragraph /StyledText  ") == Paragraph / StyledText
    assert parse_selector("Paragraph('aa') / StyledText('bb')") \
               == Paragraph.like('aa') / StyledText.like('bb')
    assert parse_selector("Paragraph('aa') / StyledText") \
               == Paragraph.like('aa') / StyledText
    assert parse_selector("Paragraph('aa' ,meh=5) / StyledText") \
               == Paragraph.like('aa', meh=5) / StyledText
    assert parse_selector("Paragraph /    StyledText('bb ') ") \
               == Paragraph / StyledText.like('bb ')
    assert parse_selector("Paragraph('aa') / ... / StyledText(blip ='blop')") \
               == Paragraph.like('aa') / ... / StyledText.like(blip='blop')
    assert parse_selector("  'paragraph' / StyledText")\
               == SelectorByName('paragraph') / StyledText
    assert parse_selector("Paragraph('aa') / ... / 'some style'") \
               == Paragraph.like('aa') / ... / SelectorByName('some style')
