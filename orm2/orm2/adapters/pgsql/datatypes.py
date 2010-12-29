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
# Revision 1.10  2006/10/07 22:06:24  diedrich
# Use datasource's psycopg_version to figure out how to handly bytea literals.
#
# Revision 1.9  2006/09/06 23:20:04  diedrich
# Fixed bytea
#
# Revision 1.8  2006/09/04 15:55:32  diedrich
# Added blob datatype that uses Python's buffer class and
# sql.direct_literal to pass binary data to psycopg's cursors directly.
#
# Revision 1.7  2006/07/08 17:10:32  diedrich
# Added bytea as alias to text
#
# Revision 1.6  2006/06/10 18:05:09  diedrich
# - Rewrote widget handling
#
# Revision 1.5  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.4  2006/05/10 21:55:41  diedrich
# Changed default for validators parameter to () rather than None
#
# Revision 1.3  2005/12/31 18:32:12  diedrich
# - Updated year in copyright header ;)
# - Fixed the serial type
#
# Revision 1.2  2005/12/18 22:35:46  diedrich
# - Inheritance
# - pgsql adapter
# - first unit tests
# - some more comments
#
# Revision 1.1  2005/11/21 19:50:23  diedrich
# Initial commit
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
from orm2 import sql
from orm2.datatypes import *
from orm2.util.fixedpoint import FixedPoint

class serial(integer):
    """
    Datatype class for PostgreSQL serial columns
    """
    def __init__(self, column=None, 
                 sequence_name=None):
        """
        @param sequence_name: The SQL identifyer of the sequence used for
           this serial. It defaults to the one created by the backend.
        """
        integer.__init__(self, column=column, title=None,
                         validators=(), has_default=True)
        self.sequence_name = sequence_name
    
    def __select_after_insert__(self, dbobj):
        # When we've already got a value, we can't be inserted again.
        
        if self.isset(dbobj):
            tpl = ( self.attribute_name,
                    self.dbclass.__name__,
                    repr(dbobj.__primary_key__), )
            
            raise ObjectAlreadyInserted(
                "Attribute %s of '%s' (%s) has already been set." % tpl)
        
        return True

    def __set__(self, dbobj, value):
        if self.isset(dbobj):
            raise ORMException( "A serial property is not mutable, " + \
                                "once it is set on object creation" )
        else:
            integer.__set__(self, dbobj, value)
    


class bytea_literal(sql.literal):
    def __init__(self, bindata):
        if type(bindata) != BufferType:
            self.bindata = buffer(bindata)
        else:
            self.bindata = bindata

    def __sql__(self, runner):
        if runner.ds.psycopg_version[0] == "1":
            from psycopg import Binary
            runner.params.append(Binary(str(self.bindata)))
        elif runner.ds.psycopg_version[0] == "2":
            runner.params.append(self.bindata)
        else:
            raise Exception("I don't know you psycopg")
            
        return "%s"

class bytea(datatype):
    python_class = str
    sql_literal_class = bytea_literal



blob = bytea

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

