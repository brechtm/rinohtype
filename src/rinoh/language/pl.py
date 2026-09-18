# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language


PL = Language('pl', 'polski',
    figure='Ilustracja',
    table='Tabela',
    contents='Spis treści',
    list_of_figures='Spis ilustracji',
    list_of_tables='Spis tabel',
    chapter='Rozdział',
    index='Skorowidz',

    # admonitions
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

    # indexes
    index_see='zobacz',
    index_seealso='zobacz również',
)
