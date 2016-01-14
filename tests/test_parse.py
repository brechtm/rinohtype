
import pytest

from rinoh.dimension import DimensionBase, PT, PICA, INCH, MM, CM, PERCENT
from rinoh.number import (NumberFormat, NUMBER, CHARACTER_LC, CHARACTER_UC,
                          ROMAN_LC, ROMAN_UC, SYMBOL)
from rinoh.flowable import HorizontalAlignment, LEFT, RIGHT, CENTER, Break, ANY
from rinoh.paragraph import TabAlign
from rinoh.style import OptionSet, Bool, Integer


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
