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

#
# $Log: datatypes.py,v $
# Revision 1.4  2007/01/22 19:46:14  diedrich
# Fixed __sql__() methods to use runner paradigm instead of the old ds.
#
# Revision 1.3  2006/07/04 22:51:49  diedrich
# Fixed validator handling.
#
# Revision 1.2  2006/05/13 14:56:36  diedrich
# Added pickle
#
# Revision 1.1  2006/04/28 08:45:50  diedrich
# Initial commit.
#
#

"""
This module defines a number of datatypes (dbattributes) for
particular purposes.
"""

from cPickle import loads, dumps, HIGHEST_PROTOCOL
from string import *

from orm2.datatypes import datatype, Unicode
from orm2.validators import *
from orm2 import sql

class idna_literal(sql.unicode_literal):
    """
    SQL literal class for <b>valid</b> Unicode (idna) domain names and
    email addresses.
    """
    def __sql__(self, runner):
        if "@" in self.content: # e-Mail address
            local, remote = split(self.content, "@")
            local = local.encode("ascii")
            remote = remote.encode("idna")

            s = "%s@%s" % ( local, remote, )
            s = runner.ds.escape_string(s)
            sql = runner.ds.string_quotes(s)
        else:
            s = self.content.encode("idna")
            s = runner.ds.escape_string(s)
            sql = runner.ds.string_quotes(s)

        return sql
            
            

class PDomain(Unicode):
    """
    Just like orm2.datatypes.Unicode, except that it doesn't use the
    backend's charset to convert the Unicode string, but Python's idna
    (Internationalized Domain Names in Applications) codec which takes
    care of lowercasing and punicode representation and so on.
    """
    sql_literal_class = idna_literal
    
    def __init__(self, column=None, title=None, validators=(),
                 widget_specs=(), has_default=False):
        
        if isinstance(validators, validator): validators = [ validators, ]
        validators = list(validators)
        validators.append(idna_fqdn_validator())
        
        Unicode.__init__(self, column, title, validators,
                         widget_specs, has_default)

    def __convert__(self, value):
        if type(value) is not UnicodeType:
            raise TypeError(
                "You must set a PDomain property to a unicode value!")
        else:
            return value


class PEMail(Unicode):
    """
    Like PDomain above, but for e-Mail addresses. The local part will be 
    checked against a regular expression, the remote part will be treated
    like a domain name by the PDomain class above.
    """
    sql_literal_class = idna_literal
    
    def __init__(self, column=None, title=None, validators=(),
                 has_default=False):

        if isinstance(validators, validator): validators = [ validators, ]
        validators = list(validators)
        validators.append(idna_email_validator())
        
        Unicode.__init__(self, column, title, validators,
                         has_default)


    def __convert__(self, value):
        if type(value) is not UnicodeType:
            raise TypeError(
                "You must set a PEMail property to a unicode value!")
        else:
            return value
        

class pickle(datatype):
    """
    This datatype uses Python's pickle module to serialize (nearly)
    arbitrary Python objects into a string representation that is then
    stored in a regular database column. See U{http://localhost/Documentation/Python/Main/lib/module-pickle.html} for details on pickling.
    """
    
    def __init__(self, pickle_protocol=HIGHEST_PROTOCOL,
                 column=None, title=None,
                 validators=(), has_default=False):
        """
        @param pickle_protocol: Version number of the protocol being used by
           the pickle functions. See U{http://localhost/Documentation/Python/Main/lib/module-pickle.html} for details. 
        """
        self.pickle_protocol = pickle_protocol
        datatype.__init__(self, column, title, validators, 
                         has_default)
        

    def __set_from_result__(self, ds, dbobj, value):
        """
        This method takes care of un-pickling the value stored in the datbase.
        """
        value = loads(value)
        setattr(dbobj, self.data_attribute_name(), value)

    def __convert__(self, value):
        """
        Since we store the Python object 'as is', convert does nothing.
        """
        return value

    def sql_literal(self, dbobj):
        """
        This function takes care of converting the Python object into a
        serialized string representation.
        """
        if not self.isset(dbobj):
            msg = "This attribute has not been retrieved from the database."
            raise AttributeError(msg)
        else:        
            value = getattr(dbobj, self.data_attribute_name())

            if value is None:
                return sql.NULL
            else:
                pickled = dumps(value, self.pickle_protocol)
                return sql.string_literal(pickled)
    
            
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

