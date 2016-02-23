# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from rinoh.template import DocumentTemplate, DocumentOptions, Option
from rinoh.text import MixedStyledText

from .base import FrontMatter, BodyMatter, BackMatter


__all__ = ['Book', 'BookOptions']


class BookOptions(DocumentOptions):
    pass


class Book(DocumentTemplate):
    sections = [FrontMatter, BodyMatter, BackMatter]
    options_class = BookOptions
