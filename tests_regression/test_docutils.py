# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from regression import render


def test_footnote_in_note(tmpdir): # issue #95
    source = ('.. note::',
              '    Here is my footnote [#qq]_.',
              '',
              '    .. [#qq] Here it is!')
    render(source, 'footnote_in_note', tmpdir)


def test_raw_role(tmpdir): # issue 99
    source = ('.. role:: raw-role(raw)',
              '   :format: html latex',
              '',
              'A paragraph containing :raw-role:`raw text`.')
    render(source, 'raw_role', tmpdir)
