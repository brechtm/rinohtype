# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.util import intersperse


def test_intersperse():
    separator = "."
    letters = [127, 0, 0, 1]
    localhost = list(intersperse(letters, separator))
    assert [127, ".", 0, ".", 0, ".", 1] == localhost
