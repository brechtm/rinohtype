# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import os

from contextlib import contextmanager
from pathlib import Path


__all__ = ['in_directory']


@contextmanager
def in_directory(path):
    curdir = Path.cwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(str(curdir))
