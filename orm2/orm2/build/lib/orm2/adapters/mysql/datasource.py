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
# Revision 1.5  2006/09/05 16:54:00  diedrich
# Of course, Python's database API doesn't support ? as a placeholder
# but %s. This also means that all %s must be escaped in input SQL. This
# remains untested for firebird.
#
# Revision 1.4  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.3  2006/05/02 13:32:01  diedrich
# Ported mysql adapter from orm v.1
#
# Revision 1.2  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
#

__docformat__ = "epytext en"

"""
This datasource module a datasource class for MySQL databases.
It relies on the  Module to connect to the backend. See
U{http://sourceforge.net/projects/mysql-python} for details.
"""

# Python
from types import *
from string import *

# MySQL
import MySQLdb # nicht als erstes Modul importieren!
from _mysql import *

# orm
import orm2.datasource
from orm2 import sql
from orm2.datatypes import common_serial
import datatypes

class datasource(orm2.datasource.datasource_base):
    
    escaped_chars = ( ('"', r'\"',),
                      ("'", r'\"',),
                      ("%", "%%",), )
    
    encodings = {"usa7": "us-ascii",
                 "big5": "big5",
                 "gbk":	"gbk",
                 "sjis": "sjis",
                 "cp932": "sjis", 
                 "cp932": "sjis", 
                 "cp932": "sjis", 
                 "gb2312": "euc_cn", 
                 "ujis": "euc_jp", 
                 "euc_kr": "euc_kr", 
                 "latin1": "iso8859_1", 
                 "latin1_de": "iso8859_1", 
                 "german1": "iso8859_1", 
                 "danish": "iso8859_1", 
                 "latin2": "iso8859_2", 
                 "czech": "iso8859_2", 
                 "hungarian": "iso8859_2", 
                 "croat": "iso8859_2", 
                 "greek": "iso8859_7",
                 "hebrew": "iso8859_8", 
                 "latin5": "iso8859_9", 
                 "latvian": "iso8859_13", 
                 "latvian1": "iso8859_13", 
                 "estonia": "iso8859_13", 
                 "dos":	"cp437", 
                 "pclatin2": "cp852",
                 "cp866": "cp866", 
                 "koi8_ru": "koi8_r", 
                 "tis620": "tis620", 
                 "win1250": "cp1250", 
                 "win1250ch": "cp1250", 
                 "win1251": "cp1251", 
                 "cp1251": "cp1251", 
                 "win1251ukr": "cp1251", 
                 "cp1257": "cp1257", 
                 "macroman": "macroman",
                 "macce": "maccentraleurope", 
                 "utf8": "utf-8", 
                 "ucs2": "unicodebig"}
 
    def __init__(self, **kwargs):
        """
        This constructor accepts all those keyword args the MySQL module's
        connect function knows about. They're passed on 'as is'. From the
        MySQL-Python documentation:
        
        Create a connection to the database. It is strongly recommended
        that you only use keyword parameters. 'NULL pointer' indicates that
        NULL will be passed to mysql_real_connect(); the value in parenthesis
        indicates how MySQL interprets the NULL. Consult the MySQL C API
        documentation for more information.

          - host -- string, host to connect to or NULL pointer (localhost)
          - user -- string, user to connect as or NULL pointer (your username)
          - passwd -- string, password to use or NULL pointer (no password)
          - db -- string, database to use or NULL (no DB selected)
          - port -- integer, TCP/IP port to connect to or default MySQL port
          - unix_socket -- string, location of unix_socket to use or use TCP
          - client_flags -- integer, flags to use or 0 (see MySQL docs)
          - conv -- conversion dictionary, see MySQLdb.converters
          - connect_time -- number of seconds to wait before the connection
            attempt fails.
          - compress -- if set, compression is enabled
          - init_command -- command which is run once the connection is created
          - read_default_file -- see the MySQL documentation for
            mysql_options()
          - read_default_group -- see the MySQL documentation for
            mysql_options()
          - cursorclass -- class object, used to create cursors or
            cursors.Cursor.
        This parameter MUST be specified as a keyword parameter.
        
        """
        orm2.datasource.datasource_base.__init__(self)
        self._connectionSpec = kwargs
        self._conn = MySQLdb.connect(**kwargs)
        self._update_cursor = self._conn.cursor()

    def _from_params(params):
        """
        Construct a mysql datasource object from an orm connection
        string. 
        
        A connection string for the mysql adapter may contain all
        keywords defined in orm2.datasource plus all those that are
        described as keyword parameters for __init__ above.        
        """
        
        if params.has_key("password"):
            passwd = params["password"]
            del params["password"]
            params["passwd"] = passwd

        if params.has_key("dbname"):
            dbname = params["dbname"]
            del params["dbname"]
            params["db"] = dbname

        return datasource(**params)
    from_params = staticmethod(_from_params)
    
    def identifyer_quotes(self, name):
        return '`%s`' % name

    #def escape_string(self, string):
    #    return self._conn.escape_string(string)
    # I'm using my own implementation, because MySQLdb uses
    # mysql_real_escape_string(), which does charset conversion. Yet, this
    # doesn't make sense on binary data for instance...
    
    def backend_encoding(self):
        name = self._conn.character_set_name()
        return self.encodings[lower(name)]
        

    def select_after_insert_where(self, dbobj):        
        if dbobj.__primary_key__ is None: raise PrimaryKeyNotKnown()
        
        primary_key_attributes = tuple(dbobj.__primary_key__.attributes())

        if len(primary_key_attributes) == 1:
            primary_key_attribute = primary_key_attributes[0]
        else:
            primary_key_attribute = None

        if isinstance(primary_key_attribute, datatypes.auto_increment) or \
               isinstance(primary_key_attribute, common_serial):
            where = sql.where(primary_key_attribute.column,
                              " = LAST_INSERT_ID()")
            
        elif dbobj.__primary_key__.isset():
            # If we know the primary key value, we use it to identify
            # the new row.
            where = dbobj.__primary_key__.where()

        else:
            raise PrimaryKeyNotKnown()
        
        return where


