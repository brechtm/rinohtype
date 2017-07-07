# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .cls import Language
from ..structure import SectionTitles, AdmonitionTitles


EN = Language('en', 'English')

SectionTitles(
    contents='Table of Contents',
    list_of_figures='List of Figures',
    list_of_tables='List of Tables',
    chapter='Chapter',
    index='Index',
) in EN

AdmonitionTitles(
    attention='Attention!',
    caution='Caution!',
    danger='!DANGER!',
    error='Error',
    hint='Hint',
    important='Important',
    note='Note',
    tip='Tip',
    warning='Warning',
    seealso='See also',
) in EN
