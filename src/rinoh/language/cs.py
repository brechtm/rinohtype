# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


CS = Language('cs', 'Česky')

SectionTitles(
    contents='Obsah',
    list_of_figures='Seznam obrázků',
    list_of_tables='Seznam tabulek',
    chapter='Kapitola',
    index='Rejstřík',
) in CS

AdmonitionTitles(
    attention='Pozor!',
    caution='Pozor!',
    danger='!NEBEZPEČÍ!',
    error='Chyba',
    hint='Poznámka',
    important='Důležité',
    note='Poznámka',
    tip='Tip',
    warning='Varování',
    seealso='Viz také',
) in CS


CS.no_break_after = ("do od u z ze za k ke o na v ve nad pod za po s se "
                     "a i že až či").split()
