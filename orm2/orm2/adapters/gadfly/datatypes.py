#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

##  This file is part of orm, The Object Relational Membrane Version 2.
##
##  Copyright 2002-2006 by Diedrich Vorberg <diedrich@tux4web.de>
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


# Changelog
# ---------
#
# $Log: datatypes.py,v $
# Revision 1.1  2006/09/04 15:54:20  diedrich
# Gadfly now manages Unicode using sql.direct_literal.
#
#
#


__docformat__ = "epytext en"

"""
This module implements datatype classes that are specific to PostgreSQL.
"""

# Python
import sys
import string
from types import *

# orm
from orm2 import datatypes
from orm2 import sql
from orm2.util.fixedpoint import FixedPoint

class Unicode(datatypes.Unicode):
    """
    The gadfly adapter defines its own Unicode type, because gadfly can't
    work with binary strings encoded as literals. This class uses
    sql.dicect_literal to pass the encoded unicode string to gadfly using
    the cursor.execute() method's '?' syntax.
    """
    python_class = unicode
    sql_literal_class = sql.direct_literal

