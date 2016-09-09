# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


FR = Language('fr', 'Français')

SectionTitles(
    contents='Table des Matières',
    chapter='Chapitre',
    index='Index',
) in FR

AdmonitionTitles(
    attention='Attention!',
    caution='Prudence!',
    danger='!DANGER!',
    error='Erreur',
    hint='Conseil',
    important='Important',
    note='Note',
    tip='Astuce',
    warning='Avertissement',
    seealso='Voir aussi',
) in FR
