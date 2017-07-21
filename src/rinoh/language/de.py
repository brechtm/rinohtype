# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


DE = Language('de', 'German')

SectionTitles(
    contents='Inhalt',
    chapter='Kapitel',
    index='Index',
) in DE

AdmonitionTitles(
    attention='Aufgepasst!',
    caution='Vorsicht!',
    danger='!GEFAHR!',
    error='Fehler',
    hint='Hinweis',
    important='Wichtig',
    note='Notiz',
    tip='Tipp',
    warning='Warnung',
    seealso='Siehe auch',
) in DE
