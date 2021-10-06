# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


__all__ = ['fully_qualified_id']


def fully_qualified_id(docname, id):
    return id if id.startswith('%') else '%' + docname + '#' + id
