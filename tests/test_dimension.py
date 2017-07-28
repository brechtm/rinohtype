# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.dimension import (DimensionAddition,
                             PT, INCH, PICA, MM, CM, PERCENT, QUARTERS)


# test operators

def test_addition():
    assert 100*PT + 10 == 110
    assert 100*PT + 10*PT == 110
    assert 100 + 10*PT ==  110
    assert 1*INCH + 8*PT == 80
    assert float(DimensionAddition()) == 0


def test_subtraction():
    assert 100*PT - 10 == 90
    assert 100*PT - 10*PT == 90
    assert 100 - 10*PT == 90
    assert 1*INCH - 2*PT == 70


def test_multiplication():
    assert 3 * 30*PT == 90
    assert 30*PT * 3 == 90


def test_division():
    assert 30*PT / 5 == 6


def test_grow():
    a = 20*PT
    a.grow(50)
    assert a == 70
    b = 20*PT
    b.grow(30*PT)
    assert b == 50
    c = 100*PT
    c.grow(-50)
    assert c == 50
    d = 100*PT
    d.grow(-30*PT)
    assert d == 70


def test_negation():
    assert -20*PT == -20


# test late evaluation

def test_late_addition():
    a = 10*PT
    b = a + 5*PT
    a.grow(2)
    assert b == 17


def test_late_subtraction():
    a = 10*PT
    b = a - 5*PT
    a.grow(2)
    assert b == 7


def test_late_multiplication():
    a = 10*PT
    b = a * 2
    a.grow(2)
    assert b == 24


def test_late_division():
    a = 10*PT
    b = a / 2
    a.grow(2)
    assert b == 6


def test_units():
    assert 4*INCH / 2 == 2*INCH
    assert 1*CM + 10*MM == 2*CM
    assert 1*PICA / 6 == 2*PT


def test_fractions():
    assert (50*PERCENT).to_points(100*PT) == 50
    assert (3*QUARTERS).to_points(100*PT) == 75
