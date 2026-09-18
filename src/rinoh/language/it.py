# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language


IT = Language('it', 'italiano',
    figure='Figura',
    table='Tabella',
    contents='Contenuti',
    list_of_figures='Elenco delle figure',
    list_of_tables='Elenco delle tabelle',
    chapter='Capitolo',
    index='Indice',

    # admonitions
    attention='Attenzione!',
    caution='Prudenza!',
    danger='!PERICOLO!',
    error='Errore',
    hint='Consiglio',
    important='Importante',
    note='Nota',
    tip='Suggerimento',
    warning='Avvertimento',
    seealso='Vedi anche',

    # indexes
    index_see='vedi',
    index_seealso='vedi anche',
)
