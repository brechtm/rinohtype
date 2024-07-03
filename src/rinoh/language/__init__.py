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
from .de import DE
from .pl import PL
from .cs import CS
from .es import ES
from .hu import HU


__all__ = ['Language', 'EN', 'FR', 'IT', 'NL', 'DE', 'PL', 'CS', 'ES', 'HU']


# generate docstrings for the Language instances

for code, language_ref in Language.languages.items():
    language = language_ref()
    lines = ['Localized strings for {}'.format(language.name)]
    for name, localized_string in language.strings.items():
        lines.append(":{}: {}".format(name, localized_string))
    language.__doc__ = '\n'.join(lines)
