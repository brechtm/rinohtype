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


class RinohWarning(Warning):
    @property
    def message(self):
        return self.args[0]


def warn(message):
    warnings.warn(RinohWarning(message))


def formatwarning(warning, category, filename, lineno, line=None):
    if category == RinohWarning:
        return '{}\n'.format(warning.message)
    else:
        return standard_formatwarning(warning, category, filename, lineno, line)


def showwarning(warning, category, filename, lineno, file=None, line=None):
    if category == RinohWarning:
        if file is None:
            file = sys.stderr
        file.write('\r' + formatwarning(warning, category, filename, line))
    else:
        return standard_showwarning(warning, category, filename, lineno, file,
                                    line)


warnings.formatwarning = formatwarning
warnings.showwarning = showwarning
