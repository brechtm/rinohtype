# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


PL = Language('pl', 'Polski')

SectionTitles(
    contents='Spis Treści',
    list_of_figures='Spis Ilustracji',
    list_of_tables='Spis Tabel',
    chapter='Rozdział',
    index='Skorowidz',
) in PL

AdmonitionTitles(
    attention='Uwaga!',
    caution='Ostrożnie!',
    danger='!NIEBEZPIECZEŃSTWO!',
    error='Błąd',
    hint='Wskazówka',
    important='Ważne',
    note='Notatka',
    tip='Porada',
    warning='Ostrzeżenie',
    seealso='Zobacz również',
) in PL
