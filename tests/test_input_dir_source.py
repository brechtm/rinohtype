# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest
from os import getcwd
from os.path import split

from rinoh.__main__ import InputDirSource


def test_input_source_root_cwd():
    path = "index.rst"
    input_dir, _ = split(path)
    source = InputDirSource(input_dir)
    assert str(source.root) == getcwd()
    assert source.location == getcwd()


def test_input_source_root():
    path = "/a/b/index.rst"
    input_dir, _ = split(path)
    source = InputDirSource(input_dir)
    assert str(source.root) == input_dir
    assert source.location == input_dir
