# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language

from .en import EN
from .fr import FR
from .it import IT
from .nl import NL


__all__ = ['Language', 'EN', 'FR', 'IT', 'NL']
