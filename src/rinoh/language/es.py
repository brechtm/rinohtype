# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles

ES = Language('es', 'Spanish')

SectionTitles(
    contents='Contenidos',
    list_of_figures='Índice de figuras',
    list_of_tables='Índice de tablas',
    chapter='Capítulo',
    index='Índice',
) in ES

AdmonitionTitles(
    attention='¡Atención!',
    caution='¡Cuidado!',
    danger='¡PELIGRO!',
    error='Error',
    hint='Pista',
    important='Importante',
    note='Nota',
    tip='Consejo',
    warning='Precaución',
    seealso='Vea también',
) in ES
