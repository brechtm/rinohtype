# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest

from helpers.regression import render_sphinx_project


def test_sphinx_minimal():
    render_sphinx_project('sphinx_minimal', 'sphinx_minimal',
                          template_cfg='sphinx_minimal.rtt')
