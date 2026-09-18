# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language


FR = Language('fr', 'français',
    figure='Figure',
    table='Tableau',
    contents='Table des matières',
    list_of_figures='Liste des figures',
    list_of_tables='Liste des tableaux',
    chapter='Chapitre',
    index='Index',

    # admonitions
    attention='Attention !',
    caution='Prudence !',
    danger='! DANGER !',
    error='Erreur',
    hint='Conseil',
    important='Important',
    note='Note',
    tip='Astuce',
    warning='Avertissement',
    seealso='Voir aussi',

    # indexes
    index_see='voir',
    index_seealso='voir aussi',
)

FR.no_break_after = "-".split()
