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


__all__ = ['Language', 'EN', 'FR', 'IT', 'NL', 'DE', 'PL']


# generate docstrings for the Language instances

for code, language_ref in Language.languages.items():
    language = language_ref()
    lines = ['Localized strings for {}'.format(language.name)]
    for string_collection in language.strings.values():
        lines.append("\n.. rubric:: {}\n"
                     .format(type(string_collection).__name__))
        for string in string_collection._strings:
            lines.append(":{}: {}".format(string.name,
                                          string_collection[string.name]))
    language.__doc__ = '\n'.join(lines)
