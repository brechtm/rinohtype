# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


IT = Language('it', 'Italiano')

SectionTitles(
    contents='Contenuti',
    chapter='Capitolo',
    index='Indice',
) in IT

AdmonitionTitles(
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
) in IT
