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
# Revision 1.16  2006/10/07 22:05:51  diedrich
# Added psycopg_version attribute.
#
# Revision 1.15  2006/09/19 14:25:25  diedrich
# Added preliminary support for psycopg2 (Zope)
#
# Revision 1.14  2006/09/05 16:54:00  diedrich
# Of course, Python's database API doesn't support ? as a placeholder
# but %s. This also means that all %s must be escaped in input SQL. This
# remains untested for firebird.
#
# Revision 1.13  2006/07/08 17:10:20  diedrich
# Added call rollback() before a db connection provided by Zope is used
#
# Revision 1.12  2006/07/04 22:47:51  diedrich
# Fixed running within Zope.
#
# Revision 1.11  2006/06/12 08:15:55  diedrich
# self._updates is not a list but a stupid_dict
#
# Revision 1.9  2006/06/09 15:37:06  diedrich
# Changed generation of default sequence names to incorporate schema names
#
# Revision 1.8  2006/06/09 09:08:08  diedrich
# Throw an exception if the backend's encoding is not known
#
# Revision 1.7  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.6  2006/05/02 13:32:43  diedrich
# select_after_insert_where() check's for the dbclass' __primary_key__
# not being None
#
# Revision 1.5  2006/04/28 09:49:26  diedrich
# Docstring updates for epydoc
#
# Revision 1.4  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.3  2005/12/31 10:03:35  diedrich
# - Added accomodation for the common_serial datatype
#
# Revision 1.2  2005/12/18 22:35:46  diedrich
# - Inheritance
# - pgsql adapter
# - first unit tests
# - some more comments
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
#

__docformat__ = "epytext en"

"""
This datasource module defines a datasource class for PostgreSQL databases.
It relies on the psycopg Module to connect to the backend. See

   - Website:  U{http://initd.org/software/initd/psycopg}
   - Download: U{http://initd.org/pub/software/psycopg/psycopg-1.0.12.tar.gz }

for details.   
"""

# Python
import sys, re
from types import *
from string import *

# Postgres
try:
    import psycopg
except ImportError:
    import psycopg2 as psycopg

# orm
from orm2.debug import sqllog, debug
from orm2.exceptions import *
from orm2 import sql
import orm2.datasource
from orm2.util import stupid_dict

from orm2.datatypes import common_serial
import datatypes

_typeoid = {}

class datasource(orm2.datasource.datasource_base):
    escaped_chars = [ ("\\", "\\\\\\\\"), ("'",  "\\'"),  ('"',  '\\"'),
                      ("\0", "\\\\000"), ("`", "\\`"), ("´", "\\´"),
                      ("\n", "\\n"), ("\r", "\\r"), ("\t", "\\t"),
                      ("%", "\\045",), ("?", "\\077",), ]

    _dbfailures = 0
    _ERRORS_BEFORE_RECONNECT = 50
    
    # Map PostgreSQL to Python encoding names. (From the PostgreSQL
    # documentation)
    encodings = \
        { "SQL_ASCII": "ascii", # ASCII
          "EUC_JP": "?", # Japanese EUC
          "EUC_CN": "?", # Chinese EUC
          "EUC_KR": "?", # Korean EUC
          "JOHAB": "?", # Korean EUC (Hangle base)
          "EUC_TW": "?", # Taiwan EUC
          "UNICODE": "utf-8", # Unicode (UTF-8)
          "UTF8": "utf-8", # Unicode (UTF-8)
          "MULE_INTERNAL": "?", # Mule internal code
          "LATIN1": "iso-8859-1", # ISO 8859-1/ECMA 94 (Latin alphabet no.1)
          "LATIN2": "iso-8859-2", # ISO 8859-2/ECMA 94 (Latin alphabet no.2)
          "LATIN3": "iso-8859-3", # ISO 8859-3/ECMA 94 (Latin alphabet no.3)
          "LATIN4": "iso-8859-4", # ISO 8859-4/ECMA 94 (Latin alphabet no.4)
          "LATIN5": "iso-8859-9", # ISO 8859-9/ECMA 128 (Latin alphabet no.5)
          "LATIN6": "iso-8859-10", # ISO 8859-10/ECMA 144 (Latin alphabet no.6)
          "LATIN7": "iso-8859-13", # ISO 8859-13 (Latin alphabet no.7)
          "LATIN8": "iso-8859-14", # ISO 8859-14 (Latin alphabet no.8)
          "LATIN9": "iso-8859-15", # ISO 8859-15 (Latin alphabet no.9)
          "LATIN10": "iso-8859-16", # ISO 8859-16/ASRO SR 14111
                                    #                    (Latin alphabet no.10)
          "ISO_8859_5": "iso-8859-5", # ISO 8859-5/ECMA 113 (Latin/Cyrillic)
          "ISO_8859_6": "iso-8859-6", # ISO 8859-6/ECMA 114 (Latin/Arabic)
          "ISO_8859_7": "iso-8859-7", # ISO 8859-7/ECMA 118 (Latin/Greek)
          "ISO_8859_8": "iso-8859-8", # ISO 8859-8/ECMA 121 (Latin/Hebrew)
          "KOI8": "?", # KOI8-R(U)
          "WIN": "?", # Windows CP1251
          "ALT": "?", # Windows CP866
          "WIN1256": "?", # Windows CP1256 (Arabic)
          "TCVN": "?", # TCVN-5712/Windows CP1258 (Vietnamese)
          "WIN874": "?" # Windows CP874 (Thai)
        }
        
    def __init__(self, dsn=None):
        """
        DSN - PostgreSLQ dsn it's basically a string like
        'field1=value field2=value' fields are describe below (from the
        pgsql Programmer's Manual):
        
        host
        ====
           Name of host to connect to. If this begins with a slash, it
           specifies Unix-domain communication rather than TCP/IP
           communication; the value bis the name of the directory in which
           the socket file is stored. The default is to connect to a
           Unix-domain socket in /tmp.  hostaddr

           IP address of host to connect to. This should be in standard
           numbers-and-dots form, as used by the BSD functions inet_aton
           et al. If a nonzero-length string is specified, TCP/IP
           communication is used.

           Using hostaddr instead of host allows the application to avoid
           a host name look-up, which may be important in applications
           with time constraints. However, Kerberos authentication
           requires the host name. The following therefore applies. If
           host is specified without hostaddr, a host name lookup is
           forced. If hostaddr is specified without host, the value for
           hostaddr gives the remote address; if Kerberos is used, this
           causes a reverse name query. If both host and hostaddr are
           specified, the value for hostaddr gives the remote address;
           the value for host is ignored, unless Kerberos is used, in
           which case that value is used for Kerberos
           authentication. Note that authentication is likely to fail if
           libpq is passed a host name that is not the name of the
           machine at hostaddr.

           Without either a host name or host address, libpq will connect
           using a local Unix domain socket.  port

           Port number to connect to at the server host, or socket file
           name extension for Unix-domain connections.

        dbname
        ======
           The database name.
        
        user
        ====
           User name to connect as.
        
        password
        ========
           Password to be used if the server demands password authentication.

        options
        =======
           Trace/debug options to be sent to the server.

        tty
        ===
           A file or tty for optional debug output from the backend.

        requiressl
        ==========
           Set to 1 to require SSL connection to the backend. Libpq will
           then refuse to connect if the server does not support SSL. Set
           to 0 (default) to negotiate with server.

        example= 'host=localhost dbname=test user=test'
        """
        orm2.datasource.datasource_base.__init__(self)

        self.psycopg_version = psycopg.__version__
        
        self._dsn = dsn        
        self._encoding = None
        self.connect()

    def _from_params(params):
        """
        A pgsql connection string may contain all the standard ORM keywords
        plus all of those described above in the __init__ method's
        doc 
        """
        if params.has_key("db"):
            dbname = params["db"]
            del params["db"]
            params["dbname"] = dbname

        dsn = []
        for a in params.items():
            dsn.append("%s=%s" % a)

        return datasource(join(dsn, " "))
    from_params = staticmethod(_from_params)

    def _from_connection(conn):
        ds = datasource(None)
        
        ds._conn = conn
        ds._update_cursor = ds._conn.cursor()

        return ds
    
    from_connection = staticmethod(_from_connection)
    
    def check_cast_handler(self, datatype_class, relation, column):
        """
        For each of the custom types register the built-in str class
        as the psycopg cast class so the SQL literal the pgsql backend
        returns can be parsed into an appropriate Python datastucture
        by our datatype and column class
        """        
        if datatype_class.sql_name:
            type_name = datatype_class.sql_name
        else:
            type_name = datatype_class.__name__
            
        if not _typeoid.has_key(type_name):
            # Run a query on the database that will return
            # the SQL type's oid. We only need the cursor's
            # description, really
            query = "SELECT %s FROM %s WHERE 0=1" % (column, relation)
            cursor = self.execute(query)
            type_oid = cursor.description[0][1]

            # register the string class with psycopg so it always 
            # returns a SQL literal as a Python string
            TYPE = psycopg.new_type((type_oid,),
                                    upper(type_name), str)
            psycopg.register_type(TYPE)

            # store the Oid in our dict 
            _typeoid[type_name] = type_oid            
    
    def dsn(self):
        """
        Return the DSN this datasource has been initialized with.
        """
        return self._dsn

    def execute(self, query, modify=False):
        """
        Run a query on the database connection.

        This function also performs failure accounting and will
        re-connect to the database if a certain threshold has passed.
        """
        if type(query) == UnicodeType:
            query = query.encode(self.backend_encoding())            
        try:
            cursor = orm2.datasource.datasource_base.execute(self, query,
                                                             modify)
        except psycopg.ProgrammingError as err:
            # In any case rollback the current transaction.
            # For one thing to get rid of that stupid "current transaction is
            # aborted, commands ignored until end of transaction block"
            self.rollback()
            
            error_message = str(err)
            if "duplicate key" in error_message:
                raise DuplicateKey(error_message, err)
            else:
                raise BackendError(error_message, err)
            
        except psycopg.Error as err:

            # if we've been constructed using fromConnection...
            if self._dsn is None:
                raise
            
            self._dbfailures += 1
            if self._dbfailures > self._ERRORS_BEFORE_RECONNECT:
                self._dbfailures = 0
                try:
                    del self._update_cursor
                    del self._conn
                    
                    self.connect()
                except:
                    raise sys.exc_type(sys.exc_value).with_traceback(sys.exc_traceback)
                
                cursor.execute(query)
            else:
                raise sys.exc_type(sys.exc_value).with_traceback(sys.exc_traceback)
            
        return cursor 
    
    def connect(self):
        if self._dsn is not None:
            self._conn = psycopg.connect(self._dsn)
            self._update_cursor = self._conn.cursor()


    def backend_version(self):
        # determine the backend's version
        cursor = self.cursor()
        cursor.execute("SELECT version()")
        result = cursor.fetchone()
        version_info = result[0]
        
        version_re = re.compile(r"PostgreSQL (\d)\.(\d)\.(\d) .*")
        result = version_re.findall(version_info)
        version = result[0]
        version = map(int, version)
        version = tuple(version)

        return version

    def backend_encoding(self):
        if self._encoding is None:
            # determine the current backend encoding
            # (this must be done backend version sensitive in the future)
            query = """SELECT pg_catalog.pg_encoding_to_char(encoding)
                         FROM pg_catalog.pg_database
                        WHERE datname = current_database()"""
            cursor = self.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            encoding = result[0]

            # hm.. let's figure out the python equivalent

            if not self.encodings.has_key(encoding):
                msg = "Unknown backend encoding %s. Most " +\
                      "probably you're running a version of PostgreSQL a " +\
                      "lot younger than your version of orm. You might want "+\
                      "to update or modify orm2/adapters/pgsql/datasource.py"+\
                      "to include the encoding in its encodings dict"
                msg = msg % encoding
                raise InternalError(msg)
            
            self._encoding = self.encodings[encoding]

        return self._encoding

    def select_after_insert_where(self, dbobj):
        if dbobj.__primary_key__ is None: raise PrimaryKeyNotKnown()
        
        primary_key_attributes = tuple(dbobj.__primary_key__.attributes())

        if len(primary_key_attributes) == 1:
            primary_key_attribute = primary_key_attributes[0]
        else:
            primary_key_attribute = None

        if isinstance(primary_key_attribute, datatypes.serial):
            # Serial columns are treated specially

            if primary_key_attribute.sequence_name is None:
                if dbobj.__relation__.schema is not None:
                    # If the relation's name is quoted and contains illegal
                    # characters for a sequence name, this wil result in an
                    # illegal identifyer. In that case please specify
                    # the sequence name by hand.
                    relation = "%s.%s" % ( dbobj.__relation__.schema,
                                           dbobj.__relation__.name.name, )
                else:
                    relation = dbobj.__relation__.name
                    
                sequence_name = "%s_%s_seq" % ( relation,
                                                primary_key_attribute.column, )
            else:
                sequence_name = primary_key_attribute.sequence_name
            
            where = sql.where(sql.expression( primary_key_attribute.column,
                                              " = ", 
                                      "currval('%s')" % (sequence_name, ) ))
            
        elif isinstance(primary_key_attribute, common_serial):
            where = sql.where(sql.expression( "id = ",
                                "currval('%s_id_seq')" % dbobj.__relation__ ))
            
        elif dbobj.__primary_key__.isset():
            # If we know the primary key value, we use it to identify
            # the new row.
            where = dbobj.__primary_key__.where()

        else:
            raise PrimaryKeyNotKnown()
        
        return where

class zpsycopg_db_conn(datasource):
    def __init__(self, context, ds_name):
        datasource.__init__(self)
        
        self.context = context
        self.ds_name = ds_name
        
        self._dbfailures = 0
        self._conn = None
        self._ERRORS_BEFORE_RECONNECT = 3
        
    def _dbconn(self):
        if self._conn is None:
            zpsycopg_obj = self.context.restrictedTraverse(
                self.ds_name)
            
            zope_conn = zpsycopg_obj()
            if hasattr(zope_conn, "getconn"):
                self._conn = zope_conn.getconn()
            else:
                self._conn = zope_conn.db
                
            self._conn.rollback()
            
        return self._conn
        
    def execute(self, query, modify=False):
        try:
            cursor = orm2.datasource.datasource_base.execute(
                self, query, modify)

        except psycopg.ProgrammingError as err:
            # In any case rollback the current transaction.
            # For one thing to get rid of that stupid "current transaction is
            # aborted, commands ignored until end of transaction block"
            self.rollback()
            
            error_message = str(err)
            if "duplicate key" in error_message:
                raise DuplicateKey(error_message, err)
            else:
                raise BackendError(error_message, err)
            
        except psycopg.Error as err:
            self._dbfailures += 1
            if self._dbfailures < self._ERRORS_BEFORE_RECONNECT:
                try:
                    if hasattr(self, "_update_cursor"):
                        del self._update_cursor
                    if hasattr(self, "db"):
                        del self._conn.db
                except:
                    raise sys.exc_type(sys.exc_value).with_traceback(sys.exc_traceback)

                self.execute(query, modify)
            else:
                raise sys.exc_type(sys.exc_value).with_traceback(sys.exc_traceback)
            
        return cursor 
            
    def rollback(self):
        """
        Undo the changes you made to the database since the last commit()
        """
        self._updates = stupid_dict()
        db = getattr(self._conn, "db", None)
        if db is not None:
            db.rollback()
        
