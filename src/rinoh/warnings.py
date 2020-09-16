# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import sys
import warnings

from warnings import formatwarning as standard_formatwarning
from warnings import showwarning as standard_showwarning


class RinohWarning(UserWarning):
    @property
    def message(self):
        return self.args[0]


def warn(message):
    warnings.warn(message, category=RinohWarning, stacklevel=2)


def showwarning(warning, category, filename, lineno, file=None, line=None):
    if category == RinohWarning:
        if file is None:
            file = sys.stderr
        file.write('\r{}\n'.format(warning.message))
    else:
        return standard_showwarning(warning, category, filename, lineno, file,
                                    line)


warnings.showwarning = showwarning
