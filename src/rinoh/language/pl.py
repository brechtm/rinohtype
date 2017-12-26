# This file is part of rinohtype, the Python document preparation system.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


PL = Language('pl', 'Polski')

SectionTitles(
    contents='Spis treści',
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
    seealso='Zobacz',
) in PL
