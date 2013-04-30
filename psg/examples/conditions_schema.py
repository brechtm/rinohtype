#!/usr/bin/python
# -*- coding: utf-8 -*-
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file gpl.txt.


#
# $Log: conditions_schema.py,v $
# Revision 1.1  2006/10/16 12:50:11  diedrich
# Initial commit
#
# Revision 1.1  2006/10/15 18:02:52  t4w00-diedrich
# Initial commit.
#
#
#

"""
In the real world, this is an orm2 database schema module (see
L{http://orm.nongnu.org/}). Here it's just a buch of classes that
implement a minimal subset of functionality so the conditions code
works and yields a lot of lorem ipsum.
"""

from lorem_ipsum import lorem_ipsum_property as lip, lorem_ipsum
from random import random


class ds:
    """
    This is a fake datasource that will return 3-6 pages with 5-14
    entries each, making sure the first is a caption and most of the
    others are info entries.
    """
    def select(self, dbclass, *args, **kw):
        ret = []

        if dbclass == page:
            num = 8 + int(random() * 4)

            for a in range(num):
                ret.append(page())
        else:
            num = 9 + int(random() * 6)

            for a in range(num):
                if len(ret) == 0 or random() > 0.95:
                    ret.append(caption_entry())
                else:
                    ret.append(info_entry())

        return ret

class _entries(ds):
    def select(self, *args, **kw):
        return ds.select(self, None)

class page:
    name = lip(3, cap=True)

    entries = _entries()

class info_entry:
    type = "info"

    value1 = lip(2, 3, cap=True)

    def get_value(self):
        if random() > 0.5:
            return "%0.2f%%" % random()
        else:
            return "%0.2f€" % random()

    value2 = property(get_value)


class caption_entry:
    type = "caption"

    value1 = lip(3, 5, cap=True)
    value2 = lip(2, 4, sentences=True)




