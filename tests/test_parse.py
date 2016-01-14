
import pytest

from rinoh.dimension import DimensionBase, PT, PICA, INCH, MM, CM, PERCENT
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
