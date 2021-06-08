# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import pytest
from os import getcwd
from os.path import split
from pathlib import Path

from rinoh.__main__ import InputDirSource


def test_input_source_root_cwd():
    path = "index.rst"
    input_dir, _ = split(path)
    source = InputDirSource(input_dir)
    assert source.root == Path.cwd()
    assert source.location == str(Path.cwd())


def test_input_source_root():
    path = "/a/b/index.rst"
    input_dir, _ = split(path)
    source = InputDirSource(input_dir)
    assert source.root == Path(input_dir)
    assert source.location == str(Path(input_dir))
