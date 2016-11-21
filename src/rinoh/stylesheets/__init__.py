# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import inspect
import os
import sys

from .. import DATA_PATH
from ..style import StyleSheetFile

from .matcher import matcher


__all__ = ['matcher', 'sphinx', 'sphinx_base14']


STYLESHEETS_PATH = os.path.join(DATA_PATH, 'stylesheets')


def path(filename):
    return os.path.join(STYLESHEETS_PATH, filename)


sphinx = StyleSheetFile(path('sphinx.rts'))

sphinx_article = StyleSheetFile(path('sphinx_article.rts'))

sphinx_base14 = StyleSheetFile(path('base14.rts'))


# generate docstrings for the StyleSheet instances

for name, stylesheet in inspect.getmembers(sys.modules[__name__]):
    if not isinstance(stylesheet, StyleSheetFile):
        continue
    stylesheet.__doc__ = ('{}\n\nEntry point name: ``{}``'
                          .format(stylesheet.description, stylesheet))
