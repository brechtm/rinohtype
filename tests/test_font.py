# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.font import Typeface, MissingGlyphException
from rinoh.font.style import FontWeight, FontSlant, FontWidth


def test_missingglyph_type1():
    times = Typeface('Times')
    font = times.get_font(weight=FontWeight.REGULAR)
    with pytest.raises(MissingGlyphException):
        font.get_glyph('\u2024', 'normal')


def test_find_closest_font():
    def second_choice(option_set, value):
        available = set(option_set.values) - set([value])
        return option_set.nearest(value, available)

    assert second_choice(FontWeight, FontWeight.REGULAR) == FontWeight.MEDIUM
    assert second_choice(FontWeight, FontWeight.MEDIUM) == FontWeight.REGULAR
    assert second_choice(FontWeight, FontWeight.BOLD) == FontWeight.SEMI_BOLD
    assert second_choice(FontWeight, FontWeight.SEMI_BOLD) == FontWeight.MEDIUM

    assert second_choice(FontSlant, FontSlant.UPRIGHT) == FontSlant.OBLIQUE
    assert second_choice(FontSlant, FontSlant.OBLIQUE) == FontSlant.ITALIC
    assert second_choice(FontSlant, FontSlant.ITALIC) == FontSlant.OBLIQUE

    assert second_choice(FontWidth, FontWidth.NORMAL) == FontWidth.SEMI_CONDENSED
    assert second_choice(FontWidth, FontWidth.SEMI_CONDENSED) == FontWidth.CONDENSED
    assert second_choice(FontWidth, FontWidth.SEMI_EXPANDED) == FontWidth.EXPANDED

    def extra_choice(option_set, value, extra):
        available = set(option_set.values) - set([value]) | set([extra])
        return option_set.nearest(value, available) == extra

    assert extra_choice(FontWeight, FontWeight.REGULAR, FontWeight.REGULAR + 5)
    assert extra_choice(FontWeight, FontWeight.MEDIUM, FontWeight.MEDIUM - 20)
