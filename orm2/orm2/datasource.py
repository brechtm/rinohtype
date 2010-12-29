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
# $Log: datasource.py,v $
# Revision 1.17  2006/10/07 22:00:55  diedrich
# Print both command and params to sqllog
#
# Revision 1.16  2006/09/05 16:54:00  diedrich
# Of course, Python's database API doesn't support ? as a placeholder
# but %s. This also means that all %s must be escaped in input SQL. This
# remains untested for firebird.
#
# Revision 1.15  2006/09/04 15:50:32  diedrich
# Updates to work with new sql.sql() class (functions to use "?" syntax in
# calls to cursor.execute()).
#
# Revision 1.14  2006/07/08 17:17:50  diedrich
# Added select_for_update() method
#
# Revision 1.13  2006/06/11 23:46:05  diedrich
# Added delete_by_primary_key()
#
# Revision 1.12  2006/06/09 09:04:20  diedrich
# Use dbclass.__result__ for results.
#
# Revision 1.11  2006/05/13 17:23:42  diedrich
# Massive docstring update.
#
# Revision 1.10  2006/05/10 21:54:15  diedrich
# Fixed a bug in flush_updates() (why did this have a cursor, attribute, anyway?)
#
# Revision 1.9  2006/04/28 08:38:30  diedrich
# Added close() method.
#
# Revision 1.8  2006/04/15 23:15:07  diedrich
# Split up select() in select() and run_select()
#
# Revision 1.7  2006/02/25 17:59:55  diedrich
# Made the many2one work with multi column keys.
#
# Revision 1.6  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.5  2006/01/01 20:38:59  diedrich
# Implemented the update machanism. Numerous misc fixes.
#
# Revision 1.4  2005/12/31 18:21:33  diedrich
# - Updated year in copyright header ;)
# - added gadfly adapter
# - added select_one() method to datasource
# - took care of situationsin which two properties refer to the same column
#
# Revision 1.3  2005/12/18 22:35:46  diedrich
# - Inheritance
# - pgsql adapter
# - first unit tests
# - some more comments
#
# Revision 1.2  2005/11/21 19:55:12  diedrich
# - put the orm2.sql specific stuff into orm2.sql (where it belongs)
# - wrote the insert() method
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#

__docformat__ = "epytext en"

"""
Defines abstract class datasource, baseclass for adapter.*.datasource.

The datasource module defines the datasource class and a number of
conveniance classes for managing query results.
"""

# Python
from types import *
import string

# orm
from orm2.debug import sqllog, debug
from orm2.exceptions import *
from orm2 import sql, keys
from orm2.util import stupid_dict

def datasource(connection_string="", **kwargs):
    """
    Return a ORM datasource object constructed from a connection
    string or a number of keyword arguments.

    The connection strings follow the conventions for PostgreSQL DSNs:
    they consist of keyword=value pairs seperated with whitespace.
    Keywords recognized are::

      adapter  - name of the ORM adapter used. Use the name from the
                 adapters/ directory.
      db       - name of the database to connect to
      user     - Database username
      password - Password used for authentication
      host     - hostname or IP address of the machine the database
                 runs on (note that there might be a difference if you
                 use 127.0.0.1 or localhost. The first creating a tcp/ip
                 connection, the latter a unix/fifo connection. This is
                 true for at leas pgsql and mysql
      debug    - if set SQL queries will be printed to stdout (actually
                 the debug.debug function is called so you can overload
                 it)

    Each of the database backends may define its own keywords. For
    instance PostgreSQL will understand each of the original keywords
    as aliases. Check the documentation!

    Values may not contain spaces.

    If you prefer to use the keyword argument syntax, the paramters must
    be the key and their arguments the values::

       datasource('db=test user=diedrich password=kfjdh')

    equals::

       datasource(db='test', user='diedrich', password='kfjdh')
    """
    
    try:
        parts = string.splitfields(connection_string)
        params = {}
        for part in parts:
            name, value = string.split(part, "=")
            if name != "" and value != "":
                params[name] = value
            else:
                raise ValueError()
    except ValueError as msg:
        raise IllegalConnectionString("%s (%s)" % (connection_string,
                                                   msg))
    
    params.update(kwargs)
    
    try:
        adapter = params["adapter"]
    except KeyError:
        raise IllegalConnectionString(
        "%s (The adapter= keyword must always be present!)" %connection_string)

    del params["adapter"]

    if adapter == "gadfly":
        from orm2.adapters.gadfly.datasource import datasource
    elif adapter == "pgsql":
        from orm2.adapters.pgsql.datasource import datasource
    elif adapter == "mysql":
        from orm2.adapters.mysql.datasource import datasource        
    elif adapter == "firebird":
        from orm2.adapters.firebird.datasource import datasource
    else:
        raise IllegalConnectionString("Unknown adapter: %s" % adapter)

    if params.has_key("debug"):
        debug = True
        del params["debug"]
    else:
        debug = False

    ds = datasource.from_params(params)
    ds._debug = debug

    return ds
    
class datasource_base(sql.datasource):
    """
    The DataSource encapsulates the functionality we need to talk to the
    database. Most notably are the insert, select and delete methods.

    This class must be subclassed by the adapter.*.datasource.datasource
    classes.

    It inherits from sql.datasource to provide default implmentations of
    the methods the sql module depends upon.
    """

    escaped_chars = [ ("\\", "\\\\"),
                      ("'",  "\\'"),
                      ('"',  '\\"'),
                      ("%", "%%",), ]

    _format_funcs = {}
    
    def __init__(self):
        self._conn = None
        self._updates = stupid_dict()
        self._update_cursor = None
        self._debug = 0    
    
    def _dbconn(self):
        """
        Return the dbconn for this ds
        """
        return self._conn
    
    def query_one(self, query):
        """        
        This method is ment for results that return exactly one row or item

        It will:
        
          - return None if there is an empty result returned
          - if there are more than one result row, return the result as is 
            (a tuple of tuples)
          - if there is only one row, but several columns, return the row as 
            a tuple
          - if the only row has only one column, return the value of the 
            column
            
        @param query:  A string containing an SQL query.
        """
        cursor = self.execute(query)
        result = cursor.fetchone()

        if len(result) == 1:
            result = result[0]
            try:
                if len(result) == 1: return result[0]
            except TypeError: # result has no size
                pass
            
            return result
        elif len(result) == 0:

            return None
        else:
            return result

    def execute(self, command, modify=False):
        """        
        Execute COMMAND on the database. If modify is True, the command
        is assumed to modify the database. All modifying commands
        will be executed on the same cursor.
        
        @param command: A string containing an SQL command of any kind or an
               sql.statement instance.
        """        
        if type(command) == UnicodeType:
            raise TypeError("Database queries must be strings, not unicode")
        
        if modify:
            cursor = self.update_cursor()
        else:
            cursor = self._dbconn().cursor()

        if isinstance(command, sql.statement):
            runner = sql.sql(self)
            command = runner(command)
            params = runner.params
        else:
            params = ()

        print >> sqllog, "command:", command, "params", repr(params)

        cursor.execute(command, tuple(params))

        print >> debug, "back!"

        return cursor
        
    def commit(self):
        """
        Run commit on this ds's connection. You need to do this for any
        change you really want to happen! 
        """
        cursor = self.flush_updates()
        self._dbconn().commit()

    def rollback(self):
        """
        Undo the changes you made to the database since the last commit()
        """
        self._updates.clear()
        self._dbconn().rollback()

    def cursor(self):
        """
        Return a newly created dbi cursor.
        """
        return self._dbconn().cursor()

    def close(self):
        """
        Close the connection to the database.
        """
        self._dbconn().close()

    def update_cursor(self):
        """
        Return the cursor that this ds uses for any query that modifies
        the database (to keep the transaction together).
        """
        if getattr(self, "_update_cursor", None) is None:
            self._update_cursor = self.cursor()

        return self._update_cursor


    def select(self, dbclass, *clauses):
        """
        SELECT dbobjs from the database, according to clauses.

        @param dbclass: The dbclass of the objects to be selected.

        @param clauses: A list of orm2.sql clauses instances (or
                        equivalent Python object i.e. strings) that
                        are added to the sql.select query.  See
                        orm2.sql.select for details

        
        """
        query = sql.select(dbclass.__select_columns__(),
                           dbclass.__relation__, *clauses)
        
        return self.run_select(dbclass, query)

    
    def run_select(self, dbclass, select):
        """
        Run a select statement on this datasource that is ment to return
        rows suitable to construct objects of dbclass from them.

        @param dbclass: The dbclass of the objects to be selected
        @param select: sql.select instance representing the query
        """
        return dbclass.__result__(self, dbclass, select)

    def select_one(self, dbclass, *clauses):
        """
        This method is ment for queries of which you know that they
        will return exactly one dbobj. It will set a limit=1 clause.
        If the result is empty, it will return None, otherwise the
        selected dbobj.
        """
        clauses += (sql.limit(1),)

        result = self.select(dbclass, *clauses)

        try:
            return result.next()
        except StopIteration:
            return None
        
    def count(self, dbclass, *clauses):
        """
        All clauses except the WHERE clause will be ignored
        (including OFFSET and LIMIT!)
        
        @param dbclass: See select() above.
        @param clauses: See select() above.
        
        @return: An integer value indicating the number of objects
                 of dbclass select() would return if run with these clauses.
        """

        where = None
        for clause in clauses:
            if isinstance(clause, sql.where):
                where = clause
                
        if where is not None:
            clauses = [where]
        else:
            clauses = []
            
        query = sql.select("COUNT(*)", dbclass.__relation__, *clauses)
        return self.query_one(query)

    def join_select(self, dbclasses, *clauses):
        # this may take some figuring
        pass

    def primary_key_where(self, dbclass, key):
        """
        Return a orm2.sql where clause that will yield the object of dbclass
        whoes primary key equals key

        @param dbclass: The dbclass of the object the where clause is
                        supposed to be for.
        @param key: Python value representing the primary key or a tuple of
          such Python values, if the primary key has multiple columns
        """

        # this function is very simmilar to keys.key.where() - maybe unify?
        
        if type(key) != TupleType: key = ( key, )
        primary_key = keys.primary_key(dbclass)

        if len(key) != len(primary_key.key_attributes):
            msg = "The primary key for %s must have %i elements." % \
                     ( repr(dbclass), len(primary_key.key_attributes), )
            raise IllegalPrimaryKey(msg)

        where = []
        for property, value in zip(primary_key.attributes(), key):
            where.append(property.column)
            where.append("=")
            where.append(property.sql_literal_class(value))
            where.append("AND")

        del where[-1] # remove last "AND"

        return sql.where(*where)
    
    def select_by_primary_key(self, dbclass, key):
        """
        Select a single object of dbclass from its relation, identified
        by its primary key.

        @param dbclass: Dbclass to be selected
        @param key: Python value representing the primary key or a tuple of
          such Python values, if the primary key has multiple columns
        @raise IllegalPrimaryKey: hallo
        @return: A single dbobj.
        """
        where = self.primary_key_where(dbclass, key)        
        result = self.select(dbclass, where)

        try:
            return result.next()
        except StopIteration:
            return None

    def select_for_update(self, dbclass, key):
        """
        This method works like L{select_by_primary_key} above, except that it
        doesn't select anything but returns a dummy object (an empty dbobj)
        that will allow setting attributes, yielding proper UPDATE statements.
        Note that supplying a primary key that does not exist will go
        unnoticed: The UPDATE statements won't create an error, they just
        won't affect any rows.

        This method is primarily ment for transaction based (i.e. www)
        applications.
        """
        if type(key) != TupleType: key = ( key, )
        primary_key = keys.primary_key(dbclass)

        if len(key) != len(primary_key.key_attributes):
            msg = "The primary key for %s must have %i elements." % \
                     ( repr(dbclass), len(primary_key.key_attributes), )
            raise IllegalPrimaryKey(msg)

        info = stupid_dict()
        for property, value in zip(primary_key.attributes(), key):        
            info[property.column] = value

        return dbclass.__from_result__(self, info)

    def insert(self, dbobj, dont_select=False):
        """
        @param dbobj: The dbobj to be inserted (must not be created by a
            select statement.
        @param dont_select: Do not perform a SELECT query for those columns
            whoes values are provided by the backend, either through
            AUTO_INCREMENT mechanisms or default column values.
        """
        if dbobj.__is_stored__():
            raise ObjectAlreadyInserted(repr(dbobj))
        
        sql_columns = []
        sql_values = []
        for property in dbobj.__dbproperties__():
            if property.isset(dbobj) and \
                   property.column not in sql_columns and \
                   property.sql_literal(dbobj) is not None:                
                sql_columns.append(property.column)
                sql_values.append(property.sql_literal(dbobj))

        if len(sql_columns) == 0:
            raise DBObjContainsNoData("Please set at least one of the attributes of this dbobj")

        statement = sql.insert(dbobj.__relation__, sql_columns, sql_values)
        self.execute(statement, modify=True)

        dbobj.__insert__(self)

        if not dont_select:
            self.select_after_insert(dbobj)

    def select_after_insert(self, dbobj):
        """
        This method will be run after each INSERT statement automaticaly
        generated by a ds to pick up default values and primary keys set
        by the backend. See insert().
        """
        properties = []
        columns = []
        for property in dbobj.__dbproperties__():
            if property.__select_after_insert__(dbobj):
                properties.append(property)
                columns.append(property.column)

        if len(properties) > 0:
            where = self.select_after_insert_where(dbobj)
            query = sql.select(columns, dbobj.__relation__, where)

            cursor = self.execute(query)
            tpl = cursor.fetchone()

            for property, value in zip(properties, tpl):
                property.__set_from_result__(self, dbobj, value)

    def select_after_insert_where(self, dbobj):
        raise NotImplemented()

    def update(self, relation, column, sql_literal, where, ):
        """
        Updates are stored in a list and executed on calls to commit() or to
        flush_updates() to join updates to the same row into a single SQL
        command.
        
        @param relation: The relation to be updated
        @param column: sql.column Name of the column to be updated
        @param sql_literal: sql literal of the value to be stored.
        @param where: where clause that would select (or update in this case)
          the desired row from relation
        """
        key = ( relation, where, )
        data = self._updates.get(key, stupid_dict())
        data[column] = sql_literal
        self._updates[key] = data
        
    def flush_updates(self):
        """
        Execute the updates stored by the update() method (see above).
        """
        for key, data_dict in self._updates.items():
            relation, where = key
            update = sql.update(relation, where, data_dict)

            self.execute(update, modify=True)

        self._updates.clear()

    def close(self):
        self._dbconn().close()        

    def delete_by_primary_key(self, dbclass, primary_key_value):
        where = self.primary_key_where(dbclass, primary_key_value)
        command = sql.delete(dbclass.__relation__, where)
        self.execute(command, True)
        
                               
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

