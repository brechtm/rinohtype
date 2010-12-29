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
# Revision 1.3  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.2  2006/05/10 21:55:41  diedrich
# Changed default for validators parameter to () rather than None
#
# Revision 1.1  2006/05/02 13:32:01  diedrich
# Ported mysql adapter from orm v.1
#
#
#
#

"""
This module implements datatype classes that are specific to MySQL
"""

# Python
import sys
from types import *
from string import *

# orm
from orm2.datatypes import *

class auto_increment(integer):
    """
    This datatype is for INTEGER columns using MySQL's AUTO_INCREMENT
    functionality. They usually serve as primary keys.
    """
    
    def __init__(self, column=None, title=None,
                 validators=(), widget_specs=()):
        integer.__init__(self, column, title, validators, widget_specs,
                         has_default=True)
    
    def __select_after_insert__(self, dbobj):
        # When we've already got a value, we can't be inserted again.        
        if self.isset(dbobj):
            tpl = ( self.attribute_name,
                    self.dbclass.__name__,
                    dbobj.__primary_key_column__(),
                    dbobj.__primary_key_literal__(), )
            
            raise ObjectAlreadyInserted(
                "Attribute %s of '%s' (%s=%s) has already been set." % tpl)
        
        return True

    def __set__(self, dbobj, value):
        if self.isset(dbobj):
            raise ORMException( "A auto_increment property is not mutable, "+\
                                "once it is on object creation" )
        else:
            integer.__set__(self, dbobj, value)
    





# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:
