

import pytest

from rinoh.dimension import (DimensionAddition,
                             PT, INCH, PICA, MM, CM, PERCENT, QUARTERS)


# test operators

def test_addition():
    assert float(100*PT + 10) == 110
    assert float(100*PT + 10*PT) == 110
    assert float(100 + 10*PT) ==  110
    assert float(1*INCH + 8*PT) == 80
    assert float(DimensionAddition()) == 0


def test_subtraction():
    assert float(100*PT - 10) == 90
    assert float(100*PT - 10*PT) == 90
    assert float(100 - 10*PT) == 90
    assert float(1*INCH - 2*PT) == 70


def test_multiplication():
    assert float(3 * 30*PT) == 90
    assert float(30*PT * 3) == 90


def test_division():
    assert float(30*PT / 5) == 6


def test_grow():
    a = 20*PT
    a.grow(50)
    assert a == 70*PT
    b = 20*PT
    b.grow(30*PT)
    assert b == 50*PT
    c = 100*PT
    c.grow(-50)
    assert c == 50*PT
    d = 100*PT
    d.grow(-30*PT)
    assert d == 70*PT


def test_negation():
    twenty = 20*PT
    assert float(-twenty) == -20


# test late evaluation

def test_late_addition():
    a = 10*PT
    b = a + 5*PT
    a.grow(2)
    assert float(b) == 17


def test_late_subtraction():
    a = 10*PT
    b = a - 5*PT
    a.grow(2)
    assert float(b) == 7


def test_late_multiplication():
    a = 10*PT
    b = a * 2
    a.grow(2)
    assert float(b) == 24


def test_late_division():
    a = 10*PT
    b = a / 2
    a.grow(2)
    assert float(b) == 6


def test_units():
    assert float(4*INCH / 2) == float(2*INCH)
    assert float(1*CM + 10*MM) == float(2*CM)
    assert float(1*PICA / 6) == float(2*PT)


def test_fractions():
    assert (50*PERCENT).to_points(100*PT) == 50
    assert (3*QUARTERS).to_points(100*PT) == 75
