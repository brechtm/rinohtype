# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language


HU = Language('hu', 'Hungarian',
    contents='Tartalomjegyzék',
    list_of_figures='Ábrák Listája',
    list_of_tables='Asztalok Listája',
    chapter='Fejezet',
    index='Index',

    # admonitions
    attention='Figyelem!',
    caution='Vigyázat!!',
    danger='!VESZÉLY!',
    error='Hiba',
    hint='Tanács',
    important='Fontos',
    note='Megjegyzés',
    tip='Tipp',
    warning='Figyelmeztetés',
    seealso='Lásd még',
)