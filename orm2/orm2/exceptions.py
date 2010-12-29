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
##  I have added a copy of the GPL in the file gpl.txt

# Changelog
# ---------
#
# $Log: exceptions.py,v $
# Revision 1.15  2006/07/08 17:07:51  diedrich
# Added DateValidatorException
#
# Revision 1.14  2006/07/05 21:40:08  diedrich
# Added NotEmptyError and ReValidatorError
#
# Revision 1.13  2006/06/09 09:05:08  diedrich
# Added InternalError exception
#
# Revision 1.12  2006/05/13 17:23:42  diedrich
# Massive docstring update.
#
# Revision 1.11  2006/05/10 21:55:10  diedrich
# Added IllegalConnectionString exception
#
# Revision 1.10  2006/04/28 09:49:27  diedrich
# Docstring updates for epydoc
#
# Revision 1.9  2006/04/28 08:43:02  diedrich
# Added NotNullError, RangeValidatorError and LengthValidatorException
#
# Revision 1.8  2006/04/21 18:54:22  diedrich
# Added validator exceptions
#
# Revision 1.7  2006/02/25 17:59:55  diedrich
# Made the many2one work with multi column keys.
#
# Revision 1.6  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.5  2006/01/01 20:42:20  diedrich
# Added ObjectMustBeInserted, DatatypeMustBeUsedInClassDefinition and
# NoDbPropertyByThatName.
#
# Revision 1.4  2005/12/31 09:58:42  diedrich
# - Added PrimaryKeyNotKnown Exception
# - Moved a number of SQL related Exceptions into that module
#
# Revision 1.3  2005/12/18 22:35:46  diedrich
# - Inheritance
# - pgsql adapter
# - first unit tests
# - some more comments
#
# Revision 1.2  2005/11/21 19:59:35  diedrich
# Added ObjectAlreadyInserted and DBObjContainsNoData
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
#
#

"""
orm2 comes with a whole bunch of exception classes, collected in this module.
"""

class ORMException(Exception):
    """
    Base class for all of orm's exceptions
    """

class InternalError(Exception):
    """
    Something inside orm has gone wrong.
    """

class IllegalConnectionString(ORMException):
    """
    This exception indicates a syntax error in a connection string
    """

class NoSuchAttributeOrColumn(ORMException):
    """
    Er... someone used an dbproperty that doesn't exist
    """

class NoPrimaryKey(ORMException):
    """
    This error is raised if a class does not have a primary key
    (__primary_key__ == None) but some function requires a primary key.
    """

class ObjectMustBeInserted(ORMException):
    """
    To perform the requested operation, the object must have been stored
    in the database.
    """

class ObjectAlreadyInserted(ORMException): 
    """
    Relationships may require dbobjects not to have been inserted into
    the database prior to handling them. Also, you can't insert an object
    into a table with a AUTO_INCREMENT column (or simmilar), that has the
    corresponding attribute set already.
    """

class DBObjContainsNoData(ORMException):
    """
    This exception is raised if a dbobj wants to be inserted that has
    none of its attributes set. If you want an empty tuple to be
    inserted to the database (to be filled with default values by the
    backend, for instance) you have to set at least one of the
    db-attributes to None.
    """

class PrimaryKeyNotKnown(ORMException):
    """
    This exception is raised when the select after insert mechanism is
    invoked on an object of which the primary key is not known and cannot
    be determined through the backend.
    """
    
class BackendError(ORMException):
    """
    The backend had something to complain
    """


class DatatypeMustBeUsedInClassDefinition(ORMException):
    """
    Most datatypes need to be part of the class definition and cannot
    be added later.
    """
        
class NoDbPropertyByThatName(ORMException):
    """
    Raised by dbobject.__dbproperty__.
    """

class SimplePrimaryKeyNeeded(ORMException):
    """
    Raised if some function expects a single column primary key but a
    multi column primary key is provided.
    """
    
class KeyNotSet(ORMException):
    """
    Raised if a key is not set or not set completely (that is, all of
    its columns)
    """

class IllegalForeignKey(ORMException):
    """
    Raised if a foreign key attribute or set of attributes doesn't match
    the attributes in the other dbclass.
    """

class ValidatorException(ORMException):
    """
    Parentclass for all those exceptions raised by validators. Those
    exceptions must always contain the dbobj, dbproperty and value
    that caused the exception along with a plausible error message(! ;-)
    This is ment to aid debugging and the creation of even more specific
    error message than a generic validator could contain. (The idea is that
    the message stored in the exception is an error for the programmer,
    the error message for the user will be created from those values).
    """
    def __init__(self, message, dbobj, dbproperty, value):
        """
        @param message: String(!) error message that goes into the regular
           exception object. This is intended for programmers (see above) and
           thus should be generic and in English.
        @param dbobj: The dbobject whoes property was supposed to be set
        @param dbproperty: The actual dbproperty that was supposed to be set
        @param value: A Python object (as opposed to a repr()) of the value
           the dbproperty was supposed to be set to
        """   
        ORMException.__init__(self, message)
        self.dbobj = dbobj
        self.dbproperty = dbproperty
        self.value = value


class NotNullError(ValidatorException):
    """
    Raised by the not_null_validator
    """
    
class NotEmptyError(ValidatorException):
    """
    Raised by the not_empty_validator
    """
    
class RangeValidatorError(ValidatorException):
    """
    Raised by range_check_validator
    """
    
class LengthValidatorException(ValidatorException):
    """
    Raised by length_validator
    """

class ReValidatorException(ValidatorException):
    def __init__(self, msg, dbobj, dbproperty, re, value):
        """
        @param re: The regular expression which has not been matched.
        """
        ValidatorException.__init__(self, msg, dbobj, dbproperty, value)
        self.re = re

class DateValidatorException(ValidatorException):
    def __init__(self, msg, dbobj, dbproperty, value, format):
        """
        @param format: Date format string as for strftime()/strptime()
        """
        ValidatorException.__init__(self, msg, dbobj, dbproperty, value)
        self.format = format
