#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

##  This file is part of orm2, The Object Relational Membrane Verion 2.
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
# $Log: sql.py,v $
# Revision 1.17  2006/09/05 16:54:00  diedrich
# Of course, Python's database API doesn't support ? as a placeholder
# but %s. This also means that all %s must be escaped in input SQL. This
# remains untested for firebird.
#
# Revision 1.16  2006/09/04 15:51:41  diedrich
# The sql.sql() class now contains functions to use "?" syntax in calls
# to cursor.execute()).
#
# Revision 1.15  2006/07/04 22:44:49  diedrich
# Added bool_literal.
#
# Revision 1.14  2006/06/11 23:46:40  diedrich
# Fixed order_by's handling of the direction param.
#
# Revision 1.13  2006/06/10 18:04:37  diedrich
# - Changed handling of relation.schema, column.relation
# - identifyer.__str__() returns name without "s
#
# Revision 1.12  2006/06/09 15:36:21  diedrich
# Added schema to relation name
#
# Revision 1.11  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.10  2006/04/28 09:49:27  diedrich
# Docstring updates for epydoc
#
# Revision 1.9  2006/04/28 08:44:48  diedrich
# Fixed __eq__()
#
# Revision 1.8  2006/02/25 17:37:39  diedrich
# Unroll lists that are passed to expression constructors
#
# Revision 1.7  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.6  2006/01/01 20:44:17  diedrich
# Added __eq__() method to _part. This had a number of consequences in
# the way columns have to be handled ourside of orm2.sql. See the
# docstrings and the stupid dict class for details.
#
# Revision 1.5  2005/12/31 18:29:38  diedrich
# - Updated year in copyright header ;)
# - Better error messages.
# - Fixed the limit and offset classes (they never worked before)
#
# Revision 1.4  2005/12/31 10:00:56  diedrich
# - Moved a number of SQL related Exceptions into this module
# - Added some more comments
#
# Revision 1.3  2005/12/18 22:35:46  diedrich
# - Inheritance
# - pgsql adapter
# - first unit tests
# - some more comments
#
# Revision 1.2  2005/11/21 20:01:09  diedrich
# - moved datasource specific stuff here
# - had clause, statement and identifyer inherift from a common baseclass,
#   that has a __str__() method. This helps me create meaningfull debug
#   messages without a real datasource
# - wrote the insert class
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
#
#

"""
This module provides a simple wrapper for SQL within Python. The idea
is to obscure the SQL code that is being generated as little as
possible, but to hide all the gorry details, especially of quoting and
escaping things, away from the programmer. Also this code is supposed
to be backend independent. Also this module is independent of the rest
of orm2.

The way it works is best described by example::

  >>> ds = datasource(...some params...)
  >>> s = select( ( quotes('first name'), 'lastname', 'age',
                   expression('age + 10'),
                   as(quotes('negative age'), 'age - 10')),
                 'person',
                 where('age > 10'), order_by('age'))
  >>> print sql(ds)(s)
  SELECT "first name", lastname, age, age + 10,
     age - 10 AS "negative age" FROM person WHERE age > 10  ORDER BY "age"
  >>> u = update( 'person', where('id = 22'),
                 firstname = string_literal('Diedrich'),
                 lastname=string_literal('Vorberg'))
  >>> print sql(ds)(u)
  UPDATE person SET lastname = 'Vorberg', firstname = 'Diedrich' WHERE id = 22
  >>> d = delete ('person', where('id = 22'))
  >>> print sql(ds)(d)
  DELETE FROM person WHERE id = 22

"""
__author__ = "Diedrich Vorberg <diedrich@tux4web.de>"
__version__ = "$Revision: 1.17 $"[11:-2]


from string import *
from types import *

NULL = "NULL" 

# Exceptions
class UnicodeNotAllowedInSQL(TypeError): pass
class SQLSyntaxError(Exception): pass
class UnicodeNotAllowedInSQL(Exception): pass
class ClauseAlreadyExists(Exception): pass 
class IllegalOrderDirection(Exception): pass


class datasource:
    """
    A mix-in class that is inherited by datasouce.datasource_base. It
    provies all the methods needed for a datasource to work with the
    sql module.

    This class' instances will work for most SQL92 complient backends
    that use utf-8 unicode encoding.
    """

    escaped_chars = ( ('"', r'\"',),
                      ("'", r'\"',),
                      ("%", "%%",), )
    
    def identifyer_quotes(self, name):
        return '"%s"' % name

    def string_quotes(self, string):
        return "'%s'" % string

    def escape_string(self, string):
        for a in self.escaped_chars:
            string = string.replace(a[0], a[1])

        return string

    def backend_encoding(self):
        return "utf-8"
    

class sql:
    """
    This class is used to do something that in Haskell is called
    Cyrrying. This is what leads to the somewhat unusual constructs in
    this source file, that look like::

      sql(ds)(some_element)

    The sql class is instantiated with ds as the constructor's
    argument. The instance implements the __call__ interface, which
    enables me to use it like a function. This 'function' is then
    applied to the some_element parameter. This is especially usefull
    when programming in a functional style as I did here.

    It takes a while to get used to this type of thinking, but it's
    certainly worthwhile. Some consider this kind of programming
    beautifull in artistic meaning of the word ;-)

    @var params: After being called, this attribute contains those parameters
       of the SQL statement that have not been escaped by this module but
       shall be passed to cursor.execute() as second argument. Corresponding
       ?s will be contained in the SQL statement.
    """
    
    def __init__(self, ds):
        if not isinstance(ds, datasource):
            raise TypeError("sql takes a datasource as argument")
        
        self.ds = ds
        self.params = []

    def __call__(self, *args):
        """
        The arguments must either provide an __sql__() function or be
        convertable to strings. The __sql__() function must return either a
        string containing SQL or a pair as ( SQL, params, ) in which params
        is a tuple which will be passed to cursor.execute() as second
        arguments. These are Python instances used by the cursor to replace
        ?s. This lets the lower level DBAPI module handle the quoting.
        """
        ret = []
        
        for arg in args:
            if type(arg) == UnicodeType:
                raise UnicodeNotAllowedInSQL()
            else:        
                if hasattr(arg, "__sql__"):
                    ret.append(arg.__sql__(self))
                else:
                    ret.append(str(arg))

        return join(ret, " ")

def flatten_identifyer_list(runner, arg):
    """
    A helper function that takes a list of strings, column and relaton
    classes and converts if it to sensible sql. 
    """
    if type(arg) in (TupleType, ListType):
        arg = map(runner, arg)
        return join(arg, ", ")
    else:
        return runner(arg)


class _part:
    """
    The _part class is the base class for all SQL statement classes.
    It proviedes a __str__() method, which calls __sql__() with a minimal
    standard datasource that will yield SQL92 compliant results.

    _part instances are not hashable. This is due to the fact that they are
    mutable and I don't want to change that. Ignoring the conflict between
    hashability and mutablity would not result in problems in many cases, but
    problems it would cause, would be *very* hard to track down (things would
    suddenly disappear from dicts, see Python Reference Manual chap. 3.3.1).

    If you need to use SQL objects as dictionary keys or sets use the
    orm2.util.stupid_dict class, which implements the mapping interface
    without relying on hashing. (It uses sequential search instead, so it's
    not suitable for large datasets.) See the datasource.select() method for
    an example on how to use stupid_dict instead of Set.
    """
    def __sql__(self, runner):
        raise NotImplementedError()

    def __str__(self):
        return sql(datasource())(self)
    
    def __eq__(self, other):
        """
        Two SQL statements are considered equal if attributes containing
        strings or statements are equal. (That means, that this method will
        be called recursivly at times.
        """
        if not isinstance(other, self.__class__):
            # Two statements must be of the same class to be
            # equal.
            return False

        for property, my_value in self.__dict__.items():
            if not other.__dict__.has_key(property):
                # If the two statements have a different set of properties,
                # they must be different.
                return False
            
            other_value = other.__dict__[property]
            
            if my_value != other_value:
                # the != above may call this function recursivly.
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)
    
class statement(_part):
    """
    Base class for all statements (select, update, delete, etc)
    """

class clause(_part):
    """
    Base class for clauses. They will be ordered according to rank
    when used to form a statement.
    """
    rank = 0

class identifyer(_part):
    """
    Base class that encapsulates all sql identifyers.
    """
    def __init__(self, name, quotes=False):
        self.name = name
        self.quotes = quotes

    def __sql__(self, runner):
        if self.quotes:
            return runner.ds.identifyer_quotes(self.name)
        else:
            return self.name

    def __str__(self):
        """
        When converted to regular strings, identifyers are not quoted.
        """
        return self.name

class quotes(identifyer):
    """
    Shorthand for an identifyer that you'd like to be surrounded in
    quotes within the sql code.
    """
    def __init__(self, name):
        identifyer.__init__(self, name, True)

class literal:
    """
    Base class for those classes that encapsulate a value that is ment
    to go into the SQL as-such.
    """
    def __init__(self, sql):
        if type(sql) == UnicodeType:
            raise UnicodeNotAllowedInSQL()
            
        self.sql = sql

    def __sql__(self, runner):
        return self.sql

class integer_literal(literal):    
    def __init__(self, i):
        if type(i) != IntType and type(i) != LongType:
            raise TypeError("integer_literal takes an integer as argument, not a " + repr(type(i)))
        self.sql = str(i)

class long_literal(literal):
    """
    Python 2.3 still makes a difference between long and int, so I need to
    classes here.
    """
    def __init__(self, i):
        if type(i) != IntType and type(i) != LongType:
            raise TypeError("long_literal takes a long as argument, not a " + repr(type(i)))
        self.sql = str(i)

class float_literal(literal):
    def __init__(self, i):
        if type(i) != FloatType and type(i) != LongType:
            raise TypeError("float_literal takes an float as argument, not a " + repr(type(i)))
        self.sql = str(i)

class string_literal(literal):
    def __init__(self, s):
        if type(s) == UnicodeType:
            raise TypeError("string_literal takes a string as argument. " + \
			    "Use unicode_literal for Unicode values.")
        
        self.content = str(s)

    def __sql__(self, runner):
        s = runner.ds.escape_string(self.content)
        sql = runner.ds.string_quotes(s)

        return sql

class unicode_literal(literal):
    def __init__(self, u):
        if type(u) != UnicodeType:
            raise TypeError("unicode_literal takes a unicode argument.")

        self.content = u

    def __sql__(self, runner):
        s = self.content.encode(runner.ds.backend_encoding())
        s = runner.ds.escape_string(s)
        sql = runner.ds.string_quotes(s)

        return sql

class bool_literal(literal):
    def __init__(self, b):
        self.content = bool(b)

    def __sql__(self, runner):
        if self.content:
            return "TRUE"
        else:
            return "FALSE"

class direct_literal(literal):
    """
    This returns a %s as SQL code and the content you pass to the constructor
    to be quoted by the cursor's implementation rathern than by orm2.sql.
    Refer to he sql class' __call__() method.
    """
    def __init__(self, content):
        self.content = content

    def __sql__(self, runner):
        runner.params.append(self.content)
        return "%s"
    
            
class relation(_part): 
    def __init__(self, name, schema=None, quote=False):
        if not isinstance(name, identifyer):
            self.name = identifyer(name, quote)
        else:
            self.name = name

        if type(schema) == StringType:
            self.schema = identifyer(schema)
        else:
            self.schema = schema

    def __sql__(self, runner):
        if self.schema is not None:
            return runner(self.schema) + "." + runner(self.name)
        else:
            return runner(self.name)

        
class column(_part):
    """
    A column name. If the relation argument is passed to the
    constructor, the sql result will look like::

       relation.column_name

    including appropriate quotes if desired. The relation parameter
    may be an sql.identifyer instance if the relation name needs to be
    quoted.
    """
    def __init__(self, name, relation=None, quote=False):
        if not isinstance(name, identifyer):
            self.name = identifyer(name, quote)
        else:
            self.name = name

        if type(relation) == StringType:
            self.relation = identifyer(relation)
        else:
            self.relation = relation

    def __sql__(self, runner):
        if self.relation is not None:
            return runner(self.relation) + "." + runner(self.name)
        else:
            return runner(self.name)

class expression:
    """
    Encapsolate an SQL expression as for example a arithmetic or a
    function call.

    >>> sql()( expression('COUNT(amount) + ', 10) )
    ==> COUNT(amount) + 10
    """
    def __init__(self, *parts):
        self.parts = []
        self._append(parts)

    def _append(self, parts):
        for part in parts:
            if type(part) in ( TupleType, ListType, GeneratorType, ):
                self._append(part)
            else:
                self.parts.append(part)

    def __sql__(self, runner):
        parts = map(runner, self.parts)
        parts = map(strip, parts)
        return join(parts, " ")

    def __add__(self, other):
        ret = expression()
        ret.parts = self.parts + other.parts

        return ret

class as_(expression):
    """
    Encapsulates an expression that goes into an AS statement in a
    SELECT's column list.

    >>> sql()( as_('column', 'columns / 10') )
    ==> columns / 10 AS column_div_by_ten

    """
    def __init__(self, column, *parts):
        self.column = column
        expression.__init__(self, *parts)

    def __sql__(self, runner):
        return expression.__sql__(self, runner)+" AS "+runner(self.column)

class where(clause, expression):
    """
    Encapsulates the WHERE clause of a SELECT, UPDATE and DELETE
    statement. Just an expression with WHERE prepended.
    """
    rank = 1

    def __sql__(self, runner):
        return "WHERE " + expression.__sql__(self, runner)

    def __add__(self, other):
        """
        Adding two where clauses connects them using AND (including
        parantheses)
        """
        ret = where()
        ret.parts = ["("] + list(self.parts) + [") AND ("] + \
                      list(other.parts) + [")"]
        return ret

    def __mul__(self, other):
        """
        Multiplying two where clauses connects them using OR (including
        parantheses). 
        """
        ret = where()
        ret.parts = ["("] + list(self.parts) + [") OR ("] + \
                       list(other.parts) + [")"]
        return ret

class order_by(clause):
    """
    Encapsulate the ORDER BY clause of a SELECT statement. Takes a
    list of columns as argument.

    FIXME: order by expression, ASC, DESC!!!
    """
    
    rank = 2
    
    def __init__(self, *columns, **kw):
        self.columns = columns

        dir = kw.get("dir", "ASC")
        if upper(dir) not in ("ASC", "DESC",):
            raise SQLSyntaxError("dir must bei either ASC or DESC")
        else:
            self.dir = dir

    def __sql__(self, runner):
        ret = "ORDER BY %s" % flatten_identifyer_list(runner, self.columns)
        
        if self.dir is not None:
            ret = "%s %s" % ( ret, self.dir, )

        return ret

orderby = order_by    

class limit(clause):
    """
    Encapsulate a SELECT statement's limit clause.
    """
    
    rank = 3
    
    def __init__(self, limit):
        if type(limit) != IntType:
            raise TypeError("Limit must be an integer")
        
        self.limit = limit

    def __sql__(self, runner):
        limit = integer_literal(self.limit)
        return "LIMIT %s" % runner(limit)

class offset(clause):
    """
    Encapsulate a SELECT statement's offset clause.
    """
    
    rank = 3
    
    def __init__(self, offset):
        if type(offset) != IntType:
            raise TypeError("Offset must be an integer")
        
        self.offset = offset

    def __sql__(self, runner):
        offset = integer_literal(self.offset)
        return "OFFSET %i" % runner(offset)

class select(statement):
    """
    Encapsulate a SELECT statement.
    """
    
    def __init__(self, columns, relations, *clauses):
        self.columns = columns
        self.relations = relations
        self.clauses = list(clauses)

        for c in self.clauses:
            if not isinstance(c, clause):
                raise TypeError("%s is not an SQL clause" % repr(c))

    def add(self, new_clause):
        if not isinstance(new_clause, clause):
            raise TypeError("Argument must be a sql clause instance.")
        
        for clause in self.clauses:
            if isinstance(new_clause, clause.__class__):
                raise ClauseAlreadyExists()

    def modify(self, new_clause):
        if not isinstance(new_clause, clause):
            raise TypeError("Argument must be a sql clause instance.")
        
        for counter, clause in self.clauses:
            if isinstance(new_clause, clause.__class__):
                del self.clauses[counter]
                break

        self.clauses.append(new_clause)

    def __sql__(self, runner):
        self.clauses.sort(lambda a, b: cmp(a.rank, b.rank))
        clauses = map(runner, self.clauses)
        clauses = join(clauses, " ")

        columns = flatten_identifyer_list(runner, self.columns)
        relations = flatten_identifyer_list(runner, self.relations)

        return "SELECT %(columns)s FROM %(relations)s %(clauses)s" % locals()

class insert(statement):
    """
    Encapsulate an INSERT statement.
    """
    def __init__(self, relation, columns, values):
        self.relation = relation
        self.columns = columns
        self.values = values

        if len(self.columns) != len(self.values):
            raise SQLSyntaxError(
                "You must provide exactly one value for each column")

    def __sql__(self, runner):
        relation = self.relation
        columns = flatten_identifyer_list(runner, self.columns)
        values = flatten_identifyer_list(runner, self.values)
        # ok, values are no identifyers, but it's really the same thing
        # that's supposed to happen with them: call sql() on each of them,
        # put a , in between and return them as a string

        return "INSERT INTO %(relation)s(%(columns)s) VALUES (%(values)s)" % \
                                                                      locals()
    
class update(statement):
    """
    Encapsulate a UPDATE statement.
    """
    
    def __init__(self, relation, where_clause, info, **param_info):
        """
        @param relation: The relation to be updates.
        @param where_clause: where clause that determines the row to be updated
        @param info: Dictionary as {'column': sql_literal}
        """
        self.relation = relation
        self.info = info
        self.info.update(param_info)

        if not isinstance(where_clause, where):
            where_clause = where(where_clause)
            
        self.where = where_clause
        
    def __sql__(self, runner):
        relation = runner(self.relation)
        where = runner(self.where)

        info = []
        for column, value in self.info.items():
            column = runner(column)
            value = runner(value)

            info.append( "%s = %s" % (column, value,) )

        info = join(info, ", ")
        
        return "UPDATE %(relation)s SET %(info)s %(where)s" % locals()


class delete(statement):
    """
    Encapsulate a DELETE statement.
    """
    
    def __init__(self, relation, where_clause):
        self.relation = relation
        self.where = where_clause

    def __sql__(self, runner):
        relation = runner(self.relation)
        where = runner(self.where)
        
        return "DELETE FROM %(relation)s %(where)s" % locals()

