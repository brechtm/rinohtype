# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from recommonmark.parser import CommonMarkParser

from ..rst import DocutilsReader


__all__ = ['CommonMarkReader']


class CommonMarkReader(DocutilsReader):
    parser_class = CommonMarkParser
