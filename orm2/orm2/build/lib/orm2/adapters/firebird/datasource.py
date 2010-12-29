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
##  I have added a copy of the GPL in the file COPYING

# Changelog
# ---------
#
# $Log: datasource.py,v $
# Revision 1.3  2006/09/05 16:54:00  diedrich
# Of course, Python's database API doesn't support ? as a placeholder
# but %s. This also means that all %s must be escaped in input SQL. This
# remains untested for firebird.
#
# Revision 1.2  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.1  2006/05/10 21:53:28  diedrich
# Initial commit
#
#
#
#

__docformat__ = "epytext en"

"""
Datasource for Firebird RDBMS
"""
import sys
from string import *

import kinterbasdb

import orm2.datasource
from orm2 import sql
from orm2.datatypes import common_serial
import datatypes

class datasource(orm2.datasource.datasource_base):

    encodings = {"ascii": "ascii",
                 "iso8859_1": "iso-8859-1",
                 "iso8859_2": "iso-8859-2",
                 "iso8859_3": "iso-8859-3",
                 "iso8859_4": "iso-8859-4",
                 "iso8859_5": "iso-8859-5",
                 "iso8859_6": "iso-8859-6",
                 "iso8859_7": "iso-8859-7",
                 "iso8859_8": "iso-8859-8",
                 "iso8859_9": "iso-8859-9",
                 "iso8859_10": "iso-8859-10",
                 "iso8859_11": "iso-8859-11",
                 "iso8859_12": "iso-8859-12",
                 "iso8859_13": "iso-8859-13",
                 "UNICODE_FSS": "utf-8" }

    def __init__(self, **kw):
        """
        This constructor supports all those key word parameters the
        kinterbas.connect() function supports:

        For details on any of these parameters see
        U{http://kinterbasdb.sourceforge.net/dist_docs/usage.html#tutorial_connect}
        
        @param dsn: A DSN pointing to the desired database
        @param user: Username
        @param password: The corresponding password
        @param host: The database host (if no DSN given)
        @param database: The database path (if no DSN given)
        @param charset: Charset for this connection. Unicode strings will be
            uncoding using this charset before they are sent to the database.
            Note that this requires a backend encoding name (see
            U{this site <http://www.firebirdsql.org/index.php?op=doc&id=fb_1_5_charsets&nosb=1>} for details.
        @param dialect: Chose the SQL dialect to use. This doesn't influence
           anything orm does (up to now).
       """
        orm2.datasource.datasource_base.__init__(self)
        self._connection_spec = kw
        self._conn = kinterbasdb.connect(**kw)
        self._update_cursor = self._conn.cursor()


        
    def _from_params(kw):
        if kw.has_key("db"):
            kw["database"] = kw["db"]
            del kw["db"]

        self = datasource(**kw)

        if kw.has_key("charset"):
            encoding = kw["charset"]
            self._backend_encoding = self.encodings.get(encoding, "ascii")
        else:
            self._backend_encoding = "iso-8859-1" # probably the most common

        return self
    
    from_params = staticmethod(_from_params)


    def backend_encoding(self):
        return self._backend_encoding

    
    def insert(self, dbobj, dont_select=False):
        """
        Firebird does not provide a mechanism that let's me query the id of
        the last row I inserted. This has to be done *before* the INSERT. 
        """

        for property in dbobj.__dbproperties__():
            if isinstance(property, common_serial):
                sequence_name = "GEN_PK_%s" % dbobj.__relation__
            elif isinstance(property, datatypes.serial):
                sequence_name = property.sequence
            else:
                continue

            query = sql.select(sql.expression("GEN_ID(", sequence_name,
                                              ", 1) AS new_id"),
                               "RDB$DATABASE")
            cursor = self.execute(query)
            tpl = cursor.fetchone()
            new_id = tpl[0]

            property.__set_from_result__(self, dbobj, new_id)
        

        orm2.datasource.datasource_base.insert(self, dbobj, dont_select)
