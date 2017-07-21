# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


NL = Language('nl', 'Nederlands')

SectionTitles(
    contents='Inhoudsopgave',
    list_of_figures='Lijst van Figuren',
    list_of_tables='Lijst van Tabellen',
    chapter='Hoofdstuk',
    index='Index',
) in NL

AdmonitionTitles(
    attention='Opgelet!',
    caution='Pas op!',
    danger='!GEVAAR!',
    error='Fout',
    hint='Hint',
    important='Belangrijk',
    note='Noot',
    tip='Tip',
    warning='Waarschuwing',
    seealso='Zie ook',
) in NL
