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
# $Log: relationships.py,v $
# Revision 1.15  2006/09/19 18:05:21  diedrich
# Many2one relationships may be set to None now.
#
# Revision 1.14  2006/07/10 22:54:59  diedrich
# Fixed typo
#
# Revision 1.13  2006/07/10 14:23:53  diedrich
# Allow access to a dbclass.__result__'s views through
# relationship.result class By adding __getattr__ to
# relationship.result.
#
# Revision 1.12  2006/07/08 17:08:42  diedrich
# Added all() to many2many relationship
#
# Revision 1.11  2006/06/10 18:09:09  diedrich
# *** empty log message ***
#
# Revision 1.10  2006/06/09 09:05:39  diedrich
# Actually use len() and __len__() as they were intended to be used
#
# Revision 1.9  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.8  2006/05/02 13:30:45  diedrich
# Make sure __len__() returns integers and that many2one.child_key is
# set to the child_class' primary key by default.
#
# Revision 1.7  2006/04/28 09:49:27  diedrich
# Docstring updates for epydoc
#
# Revision 1.6  2006/04/28 08:44:19  diedrich
# Besided some minor changes everywhere, I added the many2one relationship
#
# Revision 1.5  2006/04/15 23:20:51  diedrich
# Wrote key functionality of many2many on the way to my Mom's place...
#
# Revision 1.4  2006/02/25 18:09:08  diedrich
# Fixed small bug
#
# Revision 1.3  2006/02/25 17:59:55  diedrich
# Made the many2one work with multi column keys.
#
# Revision 1.2  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.1  2006/01/01 20:37:28  diedrich
# Initial comit (half way into many2many)
#
#
#

"""
Defines a number of classes based on L{relationship} which model how
dbclasses interrelate. 
"""

import sys
from types import *

from orm2.datatypes import datatype
from orm2.exceptions import *
from orm2 import sql, keys
from orm2.ui import view

class relationship(datatype):
    """
    Base class for all relationships.
       
    For documentation of the other parameters refer to the constructor
    of L{datatype.datatype}.
    """
    def __init__(self, child_class, child_key=None, foreign_key=None,
                 title=None, has_default=None):
        """
        @param child_class: The dbclass, this property's owner has a
          relationship to
        @param child_key: A string or a tuple of strings indicating those
           properties of the child_class that are used in the foreign key. This
           defaults to the child's primary key. The child_key must match the
           foreign_key in the number of its members and the attribute's
           datatypes.
        @param foreign_key: The foreign key. Simmlar to a dbclass' primary key
           this may be a simple string, indication the attribute that manages
           the foreign key column or a tuple of strings indicating columns
           that form the foreign key together. If the foreign key parameter is
           None __init_dbclass__() will try to guess the foreign key name as
           'child's table'_'primary key column'.

        """
        datatype.__init__(self, column=None, title=title, validators=(),
                          has_default=has_default)

        self.child_class = child_class
        self.child_key   = child_key
        self.foreign_key = foreign_key 

    # Most of the following methods are just not needed for relationship.
    # If a relationship needs them, it will redefine them anyway.
    def __set_from_result__(self, ds, dbobj, value):
        raise NotImplementedError("Not implemented by this relationship.")

    def isset(self, dbobj):
        """
        @returns: True. Most relationships are always set, even if they
           return [] or the like.
        """
        return True

    def __convert__(self, value):
        "Relationships do not need a convert method or can't use it anyway."
        raise NotImplementedError(__doc__)

    def sql_literal(self, dbobj):
        "This relationship cannot be represented as an SQL literal."
        return None

    def __select_this_column__(self):
        """
        @returns: False. Most relationships do not need to select anything.
        """
        return False

    def __select_after_insert__(self, dbobj):
        """
        @returns: False. Most relationships to not need to select anything,
          even after the insert.
        """
        return False
    
        
class _2many(relationship):

    class result(object):
        def __init__(self, dbobj, relationship):
            """
            @param dbobj: The dbobj our parent is a property of.
            @param relationship: The parent one2many relationship.
            """
            self.dbobj = dbobj
            self.relationship = relationship


        def __iter__(self):
            """
            Return those child objects that are associated with the parent's
            owner through their foreign key.
            """
            for dbobj in self.select():
                yield dbobj

        def select(self, *clauses):
            raise NotImplementedError()

        def len(self, *claises):
            raise NotImplementedError()
                        
        def append(self, *new_child_objects):
            raise NotImplementedError()
            
        def __len__(self):
            """
            Return the number of child dbobjects returned (='contained') in
            this result. Note that a call to this function will yield a SQL
            query seperate from the one used to retrieve the the actual
            objects on every call.
            """
            return int(self.len()) # some backends return long instead of int
        
        def ds(self):
            return self.dbobj.__ds__()

        def child_class(self):
            return self.relationship.child_class
        
        def where(self):
            return self.foreign_key.other_where()
        
        def add_where(self, clauses):
            """
            Add our where clause to clauses. If there is a where clause
            among the clauses already, it will be connected to our where
            clause using AND.

            @returns: A new set of clauses including the new where clause.
            """
            clauses = list(clauses)
            where = False
            for counter, clause in enumerate(clauses):
                if isinstance(clause, sql.where):
                    where = True
                    clauses[counter] = self.where() + clause

            if not where:
                clauses.append(self.where())

            return clauses

        def __getattr__(self, name):
            """
            This function allows access to a dbclass' __result__'s views
            through a relationship dbattribute.

               >>> view = parent.relationship.view()

            Will return an instance of child.__result__.view initialized
            to the current result.
            """
            dbclass = self.relationship.child_class
            
            if hasattr(dbclass.__result__, name):
                view_cls = getattr(dbclass.__result__, name)
                if type(view_cls) == ClassType and issubclass(view_cls, view):
                    return view_cls(result=self.select())
                
            else:
                raise AttributeError(name)
                

    def __init_dbclass__(self, dbclass, attribute_name):
#         self.dbclass = dbclass
#         self.attribute_name = attribute_name

#         if self.foreign_key_column is None:
#             self.foreign_key_column = "%s_%s" % (dbclass.__relation__,
#                                                  child_class.__primary_key__,)

#         if self.own_key is None:
#             self.own_key = dbclass.__dict__[dbclass.__primary_key__]
        
#         # We do not manage a column in the owner's table
#         # nor a piece of data in the owner inself.
#         # Deleting them will cause error messages on access attempts ;)
#         if hasattr(self, "column"): del self.column        
#         if hasattr(self, "_data_attribute_name"):
#             del self._data_attribute_name        
        pass

    def __get__(self, dbobj, owner):
        return self.result(dbobj, self)

    def __set__(self, dbobj, value):
        raise NotImplementedError()
    
class one2many(_2many):
    """
    A one2many relationship is probably the most common relationship between
    two tables in a RDBMS. For each row in table A table B contains zero or
    more rows. This is implemented by defining a column in table B that
    contains values that uniquly specify the row in table A they belong to.
    This is called a 'foreign key', i.e. a key that belongs to a foreign
    table.
    """

    class result(_2many.result):
        def __init__(self, dbobj, relationship):
            """
            @param dbobj: The dbobj our parent is a property of.
            @param relationship: The parent one2many relationship.
            """
            _2many.result.__init__(self, dbobj, relationship)
            
            if relationship.child_key is None:
                # guess the child key name

                try:
                    pkey_column = dbobj.__primary_key__.column()
                except SimplePrimaryKeyNeeded:
                    msg = "Can't guess foreign key column "+\
                          "name for multiple column keys %s"
                    info = repr(tuple(dbobj.__primary_key__.attribute_names()))
                    SimplePrimaryKeyNeeded(msg % info)
                    
                child_key = "%s_%s" % ( dbobj.__relation__.name,
                                        pkey_column.name, )
                
            else:
                child_key = relationship.child_key
                
            if relationship.foreign_key is None:
                foreign_key = tuple(dbobj.__primary_key__.attribute_names())
            else:
                foreign_key = relationship.foreign_key

            self.foreign_key = keys.foreign_key(dbobj,
                                                relationship.child_class,
                                                foreign_key,
                                                child_key)
        def select(self, *clauses):
            """
            This method allows you to add your own clauses to the SELECT
            SQL statement that is used to retrieve the childobjects from the
            database. This works just like the datasource's select() method,
            with two exceptions:

               - The dbclass is the relation's childclass.
               - If you supply a WHERE clause it will be added to the WHERE
                 clause generated by the one2many relationship using the AND
                 conjunction. This WHERE clause is available through this
                 class' where() method.

            Example::

              country.cities.select(order_by='name')
              
            """
            clauses = self.add_where(clauses)
            return self.ds().select(self.child_class(), *clauses)

        def len(self, *clauses):
            """
            Return the number of child objects that would be returned by
            the select() method using clauses. Note that a call to this
            function will yield a SQL query seperate from the one used to
            actually retrieve the dbobjects. (See datasource_base.count() for
            details)
            """
            clauses = self.add_where(clauses)
            return self.ds().count(self.child_class(), *clauses)

        def append(self, *new_child_objects):
            """
            Append new child objects to a one2many relationship. Those
            objects must not have been inserted into the database, yet,
            because otherwise they would just be moved from one parent object
            to the other...
            """
            for a in new_child_objects:
                if a.__class__ != self.child_class():
                    raise TypeError("You can only add %s instances to this " +\
                                    "relationship" % repr(self.child_class()))
                
                if a.__is_stored__():
                    raise ValueError("You can't append objects to a one2many"+\
                                     " relationship that are already stored"+\
                                     " in the database.")

            for a in new_child_objects:
                items = zip(self.foreign_key.other_attribute_names(),
                            self.foreign_key.values())
                for (attribute_name, value) in items:
                    setattr(a, attribute_name, value)

                self.ds().insert(a)

    def __init_dbclass__(self, dbclass, attribute_name):
        pass

    def __set__(self, dbobj, value):
        """
        Setting a one2many relationship needs three steps:

           1. value must be a list of new (not-yet inserted) child objects
           2. delete all child objects from the db
           3. insert all child objects on the list with the foreign key
              pointing to dbobj
        """        
        raise NotImplementedError("Not implemented, yet")



class many2one(relationship):
    def __init__(self, child_class, child_key=None, foreign_key=None,
                 title=None, has_default=None):
        
        relationship.__init__(self, child_class, child_key, foreign_key,
                              title, has_default)
        
        if self.child_key is None:
            child_pkey = keys.primary_key(child_class)
            self.child_key = child_pkey.attribute_names()

        if self.foreign_key is None:
            foreign_key_name = "%s_%s" % ( self.child_class.__name__,
                                           child_pkey.attribute_name(), )
            self.foreign_key = ( foreign_key_name, )
                
            
    def __set__(self, dbobj, value):
        foreign_key = keys.foreign_key(dbobj,
                                       self.child_class,
                                       self.foreign_key,
                                       self.child_key)
        
        if isinstance(value, self.child_class):
            if not value.__is_stored__():
                raise ObjectMustBeInserted("To set a many2one/one2one value "
                                           "the child object must have been "
                                           "inserted into the database.")
            setattr(dbobj, self.data_attribute_name(), value)

            for my_attr, child_attr in zip(foreign_key.my_attribute_names(),
                                          foreign_key.other_attribute_names()):
                setattr(dbobj, my_attr, getattr(value, child_attr))

        elif value is None:
            for my_attr in foreign_key.my_attribute_names():
                setattr(dbobj, my_attr, None)

            dbobj.__ds__().flush_updates()

        else:
            msg = "The %s attribute can only be set to objects of class %s"
            msg = msg % ( self.attribute_name, self.child_class.__name__, )
            raise ValueError(msg)

    def __get__(self, dbobj, owner):        
        if self.isset(dbobj):
            # If the this has run before the value has been cached
            if hasattr(dbobj, self.data_attribute_name()):
                return getattr(dbobj, self.data_attribute_name())
            else:
                foreign_key = keys.foreign_key(dbobj,
                                               self.child_class,
                                               self.foreign_key,
                                               self.child_key)
                
                child = dbobj.__ds__().select_one(self.child_class,
                                                  foreign_key.other_where())

                setattr(dbobj, self.data_attribute_name(), child)
                
                return child
                
        else:
            # this will raise an exception (w/ a complicated error message)
            relationship.__get__(self, dbobj, owner)

one2one = many2one

class many2many(_2many):
    """
    The many to many relationship manages rows from two tables which
    are linked by means of a third table, the link_relation. This tables
    stores keys from each of the tables that are to be linked. Note that
    these keys must be single column keys.

    If you set a many2many property to a list of child objects or append one
    it will be inserted into the databse if need be.

    The result class implements a subset of the list interface, but the
    lists elements are considered to have no guaranteed order (as the values
    in a dict have no order).
    """

    class result(_2many.result):
        """
        Instances of this class are returned if you __get__ a many2many
        dbproperty.
        """
        def select(self, *clauses):
            """
            Use like this:

               >>> result = dbobj.children.select(sql.where(...))

            This will yield those child objects that fit the condition
            in the where statements. Note that your WHERE will be
            integrated into a more complex WHERE clause. The many2many
            relationship uses a LEFT JOIN to connect the link_relation
            and the child relation.  You must do that by hand. Also,
            doing so might mess up your db, so you might want to use
            FOREIGN KEY constraints on the link relation.
            """
            relations = ( self.relationship.link_relation,
                          self.child_class().__relation__, ) 
            clauses = self.add_where(clauses)
            
            query = sql.select(
                self.child_class().__select_columns__(),
                relations, *clauses)

            return self.ds().run_select(
                self.child_class(), query)
                                                  

        def len(self, *clauses):
            """
            Return the number of child objects associated with a parent.
            You may supply a where clause. The same things apply as for the
            where clause for select(), see above.
            """
            clauses = self.add_where(clauses)
            
            query = sql.select("COUNT(*)",
                               ( self.relationship.link_relation,
                                 self.child_class().__relation__, ),
                               *clauses)
            
            return self.ds().query_one(query)

        def where(self):
            """
            Return the WHERE clause that selects the child objects for the
            given parent. The clause will also include the condition to limit
            the JOIN to the appropriate rows.
            """
            parent_where = sql.where(
                sql.column(self.relationship.parent_link_column(self.dbobj),
                           relation=self.relationship.link_relation),
                " = ",
                self.dbobj.__primary_key__.sql_literal())

            join_where = sql.where(
                sql.column(self.child_class().__primary_key__,
                           self.child_class().__relation__),
                " = ",
                sql.column(self.relationship.child_link_column(),
                           self.relationship.link_relation))

            return join_where + parent_where

            
        def all(self, *clauses):
            """
            This method will return all entries in the child relation (or a
            subset specified by clauses) and a list of those primary keys
            which are present in the link table. You can check if a dbobj is
            linked by doing:

                >>> result, active_keys = dbobj.relation.all()
                >>> for a in result:
                ...     if a.__primary_key__.values() in active_keys:
                ...         do_something(a)
                ...     else:
                ...         do_somethin_else(a)

            
            """
            if self.dbobj.__is_stored__():
                relations = ( self.relationship.link_relation,
                              self.child_class().__relation__, ) 
                join_clauses = self.add_where(clauses)
                
                child_pkey = keys.primary_key(self.child_class())
                query = sql.select( tuple(child_pkey.columns()),
                                    relations, *join_clauses)
                
                cursor = self.ds().execute(query)
                active_keys = list(cursor.fetchall())
            else:
                active_keys = []

            result = self.ds().select(self.child_class(), *clauses)

            return ( result, active_keys, )

        def append(self, *new_child_objects):
            """
            Appends new child objects to the parent's many2many dbproperty. 
            """
            for dbobj in new_child_objects:
                if not isinstance(dbobj, self.child_class()):
                    msg = "This relationship can only handle %s" % \
                                           repr(self.child_class())
                    raise TypeError(msg)

                if not dbobj.__is_stored__():
                    # The many2many relationship will insert fresh objects
                    # into the database.
                    self.ds().insert(dbobj)

                # insert a row into the link_relation
                command = sql.insert(self.relationship.link_relation,
                  ( self.relationship.parent_link_column(self.dbobj),
                    self.relationship.child_link_column(), ),
                  ( self.relationship.parent_own_key(
                                         self.dbobj).sql_literal(self.dbobj),
                    self.relationship.child_own_key().sql_literal(dbobj), ))
                
                self.ds().execute(command)

        def unlink(self, child_object):
            """
            Remove the entry from the link relation that links it to the
            parent dbobj.
            """
            self.unlink_by_primary_key(
                             child_object.__primary_key__.sql_literal())
            
        def unlink_by_primary_key(self, pkey):
            """
            Remove an entry from the link relation that links the parent
            dbobj to a child identfyed by pkey

            @param pkey: An sql.literal instance
            """
            if not isinstance(pkey, sql.literal):
                raise TypeError("pkey must be an sql.literal instance!")
            
            cmd = sql.delete(self.relationship.link_relation,
                    sql.where(self.relationship.parent_link_column(self.dbobj),
                              " = ",
                              self.dbobj.__primary_key__.sql_literal(),
                              " AND ",
                              self.relationship.child_link_column(),
                              " = ",
                              pkey))
                             
            self.ds().execute(cmd)
            
            
    
    def __init__(self, child_class, link_relation,
                 parent_own_key=None, parent_link_column=None,
                 child_own_key=None, child_link_column=None,
                 title=None):
        """
        @param parent_own_key: The attribute in the parent dbclass that
          is referred to by the link table. Defaults to the primary key.
        @param parent_link_column: The column name(!) in the link table
          referring to parent_own_key. Defaults to
          <parent class name>_<primary key column>.
        @param child_own_key: The attribute in the child dbclass that
          is referred to by the link table. Defaults to the primary key.
        @param child_link_column: The column name(!) in the link table
          referring to child_own_key. Defaults to
          <child class name>_<child key column>.
        """
        relationship.__init__(self, child_class, None, None,
                              title, False)

        if isinstance(link_relation, sql.relation):
            self.link_relation = link_relation
        else:
            self.link_relation = sql.relation(link_relation)
        
        self._parent_own_key = parent_own_key
        
        if isinstance(parent_link_column, sql.column):
            self._parent_link_column = parent_link_column.column
        else:
            self._parent_link_column = parent_link_column
            
        self._child_own_key = child_own_key

        if isinstance(child_link_column, sql.column):
            self._child_link_column = child_link_column.column
        else:
            self._child_link_column = child_link_column

            
    def __set__(self, dbobj, value):
        # make sure value is a sequence.
        try:
            value = list(value) 
        except TypeError:
            raise ValueError("You must assing a sequence of %s to this dbproperty!" % repr(self.child_class))
            
        # delete all links from the link_relation that point to the dbobj
        command = sql.delete(self.link_relation,
                             sql.where(self.parent_link_column(dbobj),
                                       " = ",
                                       dbobj.__primary_key__.sql_literal()))
        dbobj.__ds__().execute(command)

        # use the result class to (re-)insert the links
        result = self.result(dbobj, self)

        result.append(*value)
        
    def reverse(cls, original_dbclass, attribute_name,
                title=None):
        """
        Constructor.
        
        A little helper function: If you've defined one many2many relation,
        this constructor will take it as an argument and return the
        complimentary one to be an attribute in the child class.

        @param original_dbclass: dbclass you've already defined a many2many
           relationship for.
        @param attribute_name: Attribute name of the many2many relationship
          in the original dbclass.
        """
        
        original = original_dbclass.__dbproperty__(attribute_name)

        return many2many(original_dbclass,
                         original.link_relation,
                         original._child_own_key,
                         original._child_link_column,
                         original._parent_own_key,
                         original._parent_link_column,
                         title)
    
    reverse = classmethod(reverse)
                          
    def parent_own_key(self, dbobj):
        if self._parent_own_key is None:
            return dbobj.__primary_key__.attribute()
        else:
            return dbobj.__dbproperty__(self._parent_own_key)

    def parent_link_column(self, dbobj):
        if self._parent_link_column is None:
            return "%s_%s" % ( dbobj.__class__.__name__,
                               dbobj.__primary_key__.column().name, )
        else:
            return self._parent_link_column

    def child_own_key(self):
        if self._child_own_key is None:
            return self.child_class.__dbproperty__()
        else:
            return self.child_class.__dbproperty__(self._child_own_key)

    def child_link_column(self):
        if type(self.child_class.__primary_key__) != StringType:
            raise SimplePrimaryKeyNeeded("in %s" % repr(self.child_class))

        if self._child_link_column is None:
            return "%s_%s" % ( self.child_class.__name__,
                               self.child_class.__primary_key__, )
        else:
            return self._child_link_column


        

class many2one(relationship):
    def __init__(self, child_class, 
                 child_key=None, foreign_key=None, column=None,
                 title=None, has_default=None,
                 cache=True):
        """
        @param cache: Indicates whether the relationship object shall
           keep a copy of the child object in the dbobj for faster access.
        """
        if foreign_key is not None and column is not None:
            raise Exception("You can't specify both a foreign_key (based"+\
                            " on attribute names) and an SQL column for "+\
                            " a many2one relationship")

        datatype.__init__(self, column, title, (), has_default)

        if foreign_key is None:
            pk = keys.primary_key(child_class)
            self.python_class = pk.attribute().python_class
            self.sql_literal_class = pk.attribute().sql_literal_class
        
        self.child_class = child_class

        if child_key is None:
            self.child_key = child_class.__primary_key__
        else:
            self.child_key = child_key

        self.foreign_key = foreign_key
        
        self.cache = cache
        
    def __set_from_result__(self, ds, dbobj, value):
        setattr(dbobj, self.data_attribute_name(), value)

    def __init_dbclass__(self, dbclass, attribute_name):
        if self.column is None and self.foreign_key is None:
            column_name = "%s_%s" % ( self.child_class.__name__,
                                      self.child_class.__primary_key__)
                          # A class' __primary_key__ attr is always a string!

            self.column = sql.column(column_name)
            
        datatype.__init_dbclass__(self, dbclass, attribute_name)
        
        if self.foreign_key is not None:
            self.column = None
            


    def __get__(self, dbobj, owner):
        if self.cache and \
               hasattr(dbobj, self.data_attribute_name() + "_cache"):
            return getattr(dbobj, self.data_attribute_name() + "_cache")
        
        ds = dbobj.__ds__()
        
        if self.column is not None:
            value = datatype.__get__(self, dbobj)
            ret = ds.select_by_primary_key(self.child_class, value)
        else:
            foreign_key = keys.foreign_key(dbobj, self.child_class,
                                           self.foreign_key, self.child_key)
        
            # Ok, let's check some exception condition...
            set_count = 0
            none_count = 0
            for attr in foreign_key.my_attributes():
                if attr.__get__(dbobj) is None:
                    none_count += 1
                else:
                    set_count += 1

            if set_count == 0:
                return None # a many2one attribute with a multi column key
                            # is considered None, if all key attributes are
                            # None


            if none_count != 0:
                # If some of the key attributes are None, and some are set,
                # it is considered an error
                raise IllegalForeignKey("For a many2one relationship with a "+\
                                        "multi column key, either all attrs "+\
                                        "must be set or all must be None.")
            
            result = ds.select(self.child_class,
                               foreign_key.other_where())

            try:
                ret = result.next()
            except StopIteration:
                raise IllegalForeignKey("The foreign key you set for " + \
                                        repr(dbobj) + " does not refer to " + \
                                        "exaxtly one child object")

        if self.cache:
            setattr(dbobj, self.data_attribute_name() + "_cache", ret)

        return ret

    def __set__(self, dbobj, value):
        """
        Set the child object to `value'. If the child object has not been
        inserted, yet it will be by this function.
        """
        if value is None:
            if self.column is not None:
                datatype.__set__(self, dbobj, None)
            else:
                foreign_key = keys.foreign_key(dbobj, self.child_class,
                                               self.foreign_key,
                                               self.child_key)
        
                for prop in foreign_key.my_attributes():
                    prop.__set__(dbobj, None)
                    
            if hasattr(dbobj, self.data_attribute_name() + "_cache"):
                delattr(dbobj, self.data_attribute_name() + "_cache")
        else:            
            if not isinstance(value, self.child_class):
                raise TypeError("A many2one attribute can only be set to " + \
                                self.child_class.__name__, " + instances")

            if not value.__is_stored__():
                self.__ds__().insert(value)

            if self.column is not None:
                datatype.__set__(self, dbobj, value.__primary_key__.
                                               attribute().__get__(value))
            else:
                foreign_key = keys.foreign_key(dbobj, self.child_class,
                                               self.foreign_key,
                                               self.child_key)        
                
                for my, other in zip(foreign_key.my_attributes(),
                                     foreign_key.other_attributes()):
                    my.__set__(dbobj, other.__get__(value))

            if self.cache:
                setattr(dbobj, self.data_attribute_name() + "_cache", value)


    def isset(self, dbobj):
        if self.column is not None:
            return datatype.isset(self, dbobj)
        else:
            foreign_key = keys.foreign_key(dbobj, self.child_class,
                                           self.foreign_key, self.child_key)

            return foreign_key.isset()

    def __convert__(self, value):
        if not isinstance(self.child_class.__primary_key__, keys.primary_key):
            return value
        else:
            return self.child_class.__primary_key__.attributes().\
                                                       __convert__(value)
    
    def sql_literal(self, dbobj):
        if self.column is None:
            return None # We don't INSERT anything
        else:
            return datatype.sql_literal(self, dbobj)

    def __select_this_column__(self):
        if self.column is not None:
            return True
        else:
            return False

    
    
        
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:


