# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language


PL = Language('pl', 'Polski',
    figure='Ilustracja',
    table='Tabela',
    contents='Spis Treści',
    list_of_figures='Spis Ilustracji',
    list_of_tables='Spis Tabel',
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
)
