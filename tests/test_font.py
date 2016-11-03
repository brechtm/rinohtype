# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from rinoh.font import Typeface, MissingGlyphException


def test_missingglyph_type1():
    times = Typeface('Times')
    font = times.get_font(weight='regular')
    with pytest.raises(MissingGlyphException):
        font.get_glyph('\u2024', 'normal')
