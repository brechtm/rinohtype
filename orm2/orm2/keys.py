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

"""
This module defines helper classes that handle SQL primary and foreign
keys.
"""

from types import *
from string import *

import sql
from exceptions import *

class key:
    """
    This class manages keys of dbobjects (not dbclasses! The object must be
    initialized for this to work). It is instantiated by dbobject.__init__(),
    among others, using the __primary_key__ attribute to set it up.

    There are a number of methods in this class which come in pairs: a
    singular one and a plural one. attribute() for instance returns returns
    the name of the dbobj's key attribute, if, and only if, the key is a
    single column key. If the key has multiple column, it will raise an
    exception. This is true also for column() and value(). The plural form
    of these functions is more generic: it will return a generator(!) yielding
    the requested objects, a generator with only one element for single column
    keys, a generator with several element for multiple column keys.

    I know the way this is imlemented below duplicates a lot of code
    and could be optimized. But since this would make the code much
    harder to understand and these functions are not likely to change
    in principle, I've decided to write it this way.
    """
    
    def __init__(self, dbobj, *key_attributes):
        """
        @param dbobj: Dbobj  that this key belongs to. (If you pass a dbclass
           instead of a dbobj, all functionality will work that doesn't
           depend on actual data).
        @param key_attributes: Those attribute(s) the key consists of
        """
        self.dbobj = dbobj
        
        if len(key_attributes) == 0:
            raise ValueError("The primary key must have at least one " + \
                             "column (attribtue)!")

        # check if all the attributes are in the dbobj...
        for attribute in key_attributes:
            # If there is an unknown attribute in the key_attributes list
            # (a typo maybe), this will raise an NoDbPropertyByThatName
            # exception.
            dbobj.__dbproperty__(attribute)

        self.key_attributes = key_attributes

    def isset(self):
        """
        @returns: True, if all attributes that are needed for this key are
           set within the dbobj.
        """
        for attribute in self.key_attributes:
            dbproperty = self.dbobj.__dbproperty__(attribute)
            if not dbproperty.isset(self.dbobj):
                return False

        return True
            
    def attribute_name(self):
        """
        @returns: An string containing the name of the attribute managing
            the key column.
        @raises SimplePrimaryKeyNeeded: if the key is a multiple attribute key
        """
        if len(self.key_attributes) != 1:
            msg = "%s not a single attribute key" % repr(self.key_attributes)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.key_attributes[0]

    def attribute_names(self):
        """
        @returns: A tuple of strings naming the db attributes managing the
            key columns.
        """
        return tuple(self.key_attributes) 

    def attribute(self):
        """
        @returns: An datatype instance managing the key attribute.
        @raises SimplePrimaryKeyNeeded: if the key is a multiple attribute key
        """
        if len(self.key_attributes) != 1:
            msg = "%s not a single attribute key" % repr(self.key_attributes)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.attributes().next()

    def attributes(self):
        """
        @returns: A generator yielding the datatype instances that comprise
            the key
        """
        for attribute in self.key_attributes:
            yield self.dbobj.__dbproperty__(attribute)

    def column(self):
        """
        @returns: An sql.column instance indicating the key's column.
        @raises SimplePrimaryKeyNeeded: if the key is a multiple column key
        """
        if len(self.key_attributes) != 1:
            msg = "%s not a single column key" % repr(self.key_columns)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.columns().next()

    def columns(self):
        """
        @returns: A tuple of sql.column instances that comprise the key
        """
        for attribute in self.key_attributes:
            dbproperty = self.dbobj.__dbproperty__(attribute)
            yield dbproperty.column

    def value(self):
        """
        @returns: The value of the key as a Python data object
        @raises SimplePrimaryKeyNeeded: if the key is a multiple column key
        """
        if len(self.key_attributes) != 1:
            msg = "%s not a single column key" % repr(self.key_columns)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.values().next()

    def values(self):
        """
        @returns: The value of the key as Python tuple
        """
        if not self.isset():
            raise KeyNotSet()

        ret = []
        for attribute in self.key_attributes:
            ret.append(getattr(self.dbobj, attribute))

        return tuple(ret)

    def sql_literal(self):
        """
        @returns: The sql_literal of the key as a Python data object
        @raises SimplePrimaryKeyNeeded: if the key is a multiple column key
        """
        if len(self.key_attributes) != 1:
            msg = "%s not a single column key" % repr(self.key_columns)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.sql_literals().next()

    def sql_literals(self):
        """
        @returns: A generator yielding the SQL literals of this key as
           strings.
        """
        if not self.isset():
            raise KeyNotSet()

        for attribute in self.key_attributes:
            dbproperty = self.dbobj.__dbproperty__(attribute)
            yield dbproperty.sql_literal(self.dbobj)

        
    def _where(self, columns):
        if not self.isset():
            raise KeyNotSet()

        literals = self.sql_literals()

        where = []
        for column, literal in zip(columns, literals):
            where.append(column)
            where.append("=")
            where.append(literal)
            where.append("AND")

        del where[-1] # remove the straneous AND

        return sql.where(*where)

    def where(self):
        """
        @returns: sql.where() instance representing a where clause that
           refers to this key
        """
        return self._where(self.columns())
    
    def __eq__(self, other):
        """
        @returns: True - if the other refers to the same key (maybe
        different tables!) as this key, otherwise, you guessed it,
        False.  Order of attributes (i.e. columns) does matter, as it
        does in SQL!
        """
        me = tuple(self.values())
        other = tuple(other.values())

        return me == other

    def make_tuple(self, t):
        error = False
        
        if type(t) == StringType:
            return (t,)
        
        elif type(t) == TupleType:
            # check if all members of the tuple are strings
            for a in t:
                if type(a) != StringType:
                    error = True
            
        else: # all other types raise a TypeError exception
            error = True

        if error:
            raise TypeError("A key must be either a single string indicating"+\
                            " an attribute or a tuple of simple strings" + \
                            ", not %s" % repr(t))

        return t


class primary_key(key):
    def __init__(self, dbobj):
        pkey = self.make_tuple(dbobj.__primary_key__)
        key.__init__(self, dbobj, *pkey)


class foreign_key(key):
    """
    The foreign key class knows about two objects: 'me' and
    'other'. 'Me' is the dbobj it belongs to (the relataionship's
    parent object) and 'other' the one that the key refers to (the
    relationship's child object(s)). The key class's methods
    attribute[s](), column[s]() and where() refer to the parent object
    and are also aliased by the my_attribute[s] (etc..) methods. The
    other_attribute[s] (etc..) methods refer to the child
    object. Thode methods that yield actual data values need not to be
    duplicated, because those values are the same in parent and child
    objects, of course.
    """
    def __init__(self, my_dbobj, other_dbclass,
                 my_key_attributes, other_key_attributes):
        """
        Each of the attributes sets must point to the same datatypes
        in the same order to function properly as a foreign key!
        
        @param my_dbobj: The parent dbobj
        @param child_dbclass: The child's dbclass (not object...!)
        @param my_key_attributes: A tuple of string(s) refering to those
           of the parent's properties that manage the key column(s).
        @param other_key_attributes: A tuple of string(s) refering to those
           of the child's properties that manage the key column(s).
        """
        my_key_attributes = self.make_tuple(my_key_attributes)
        other_key_attributes = self.make_tuple(other_key_attributes)
        
        if len(my_key_attributes) != len(other_key_attributes):
            msg = "The number of key attributes (columns) " + \
                  "does not match (%s, %s)"
            raise IllegalForeignKey(msg % ( repr(my_key_attributes),
                                            repr(other_key_attributes), ))

        for my, other in zip(my_key_attributes, other_key_attributes):
            my_prp = my_dbobj.__dbproperty__(my)
            other_prp = other_dbclass.__dbproperty__(other)

            if my_prp.__class__ != other_prp.__class__:
                msg = "Property datatypes do not match for foreign key " + \
                      "%s (%s) != %s (%s)" % ( my, repr(my_prp),
                                               other, repr(other_prp), )
                IllegalForeignKey(msg)
        
        key.__init__(self, my_dbobj, *my_key_attributes)
        self.other_key_attributes = other_key_attributes
        self.other_dbclass = other_dbclass

    my_attribute_name = key.attribute_name
    my_attribute_names = key.attribute_names
    my_attribute = key.attribute
    my_attributes = key.attributes
    my_column = key.column
    my_columns = key.columns
    my_where = key.where

    def other_attribute_name(self):
        """
        @returns: An string containing the name of the attribute managing
            the key column.
        @raises SimplePrimaryKeyNeeded: if the key is a multiple attribute key
        """
        if len(self.other_key_attributes) != 1:
            msg = "%s not a single attribute key" % repr(self.key_attributes)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.other_key_attributes[0]

    def other_attribute_names(self):
        """
        @returns: A tuple of strings naming the db attributes managing the
            key columns.
        """
        return tuple(self.other_key_attributes) 

    def other_attribute(self):
        """
        @returns: An datatype instance managing the key attribute.
        @raises SimplePrimaryKeyNeeded: if the key is a multiple attribute key
        """
        if len(self.other_key_attributes) != 1:
            msg = "%s not a single attribute key" % repr(self.key_attributes)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.other_attributes.next()

    def other_attributes(self):
        """
        @returns: A generator yielding the datatype instances that comprise
            the key
        """
        for attribute in self.other_key_attributes:
            yield self.other_dbclass.__dbproperty__(attribute)

    def other_column(self):
        """
        @returns: An sql.column instance indicating the key's column.
        @raises SimplePrimaryKeyNeeded: if the key is a multiple column key
        """
        if len(self.other_key_attributes) != 1:
            msg = "%s not a single column key" % repr(self.key_columns)
            raise SimplePrimaryKeyNeeded(msg)
        else:
            return self.other_columns().next()

    def other_columns(self):
        """
        @returns: A tuple of sql.column instances that comprise the key
        """
        for attribute in self.other_key_attributes:
            dbproperty = self.other_dbclass.__dbproperty__(attribute)
            yield dbproperty.column
    
    def other_where(self):
        """
        @returns: sql.where() instance representing a where clause that
           refers to this key in the 'other' (child) relation
        """
        return self._where(self.other_columns())
    
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

