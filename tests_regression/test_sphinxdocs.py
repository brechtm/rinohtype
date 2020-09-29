# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import pytest

from pathlib import Path

from helpers.regression import render_sphinx_project


@pytest.mark.longrunning
def test_sphinxdocs():
    render_sphinx_project('sphinx', Path('sphinx') / 'doc',
                        template_cfg='sphinxdocs.rtt')
