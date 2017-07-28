# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest


from rinoh.color import Color, HexColor, Gray


def test_components():
    for r, g, b in [(1, 0.1, 0.8), (0.12, 0.0001, 0.008), (0.87, 0.4, 0.3)]:
        color = Color(r, g, b)
        assert color.r == r
        assert color.g == g
        assert color.b == b
        assert color.a == 1.0

    for r, g, b, a in [(0.5, 0.4, 0.3, 0.2), (0.2, 0.4, 0.6, 0.8)]:
        color = Color(r, g, b, a)
        assert color.r == r
        assert color.g == g
        assert color.b == b
        assert color.a == a


def test_bad_value():
    for values in [(-0.1, 0, 0),
                   (1, float('+inf'), 0),
                   (0, 0, 1.01),
                   (0.5, 0.5, 0.5, 2.0)]:
        with pytest.raises(ValueError):
            Color(*values)


def test_hex_color():
    color = HexColor('#1023F6')
    assert color.r == 0x10 / 255
    assert color.g == 0x23 / 255
    assert color.b == 0xF6 / 255
    assert color.a == 1.0
    assert str(color) == '#1023f6'

    color2 = HexColor('E30BCAD7')
    assert color2.r == 0xE3 / 255
    assert color2.g == 0x0B / 255
    assert color2.b == 0xCA / 255
    assert color2.a == 0xD7 / 255
    assert str(color2) == '#e30bcad7'


def test_short_hex_color():
    color3 = HexColor('#A49')
    assert color3.r == 0xAA / 255
    assert color3.g == 0x44 / 255
    assert color3.b == 0x99 / 255
    assert str(color3) == '#a49'

    color4 = HexColor('#2c6e')
    assert color4.r == 0x22 / 255
    assert color4.g == 0xCC / 255
    assert color4.b == 0x66 / 255
    assert color4.a == 0xEE / 255
    assert str(color4) == '#2c6e'


def test_bad_hex_value():
    for hex_string in ['', 'zz0000', '0011223', 'a', '0011223344']:
        with pytest.raises(ValueError):
            HexColor(hex_string)


def test_gray():
    for luminance in (1.0, 0.37, 0.987):
        gray = Gray(luminance)
        assert gray.r == luminance
        assert gray.g == luminance
        assert gray.b == luminance
        assert gray.a == 1.0

    for luminance, alpha in [(0.8, 0.2), (0.1, 0), (0.14159, 0.999)]:
        gray = Gray(luminance, alpha)
        assert gray.r == luminance
        assert gray.g == luminance
        assert gray.b == luminance
        assert gray.a == alpha
