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
# $Log: datatypes.py,v $
# Revision 1.2  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.1  2006/05/10 21:53:28  diedrich
# Initial commit
#
#
#
#

"""
This module defines those datatypes that are specific for FireBird.

@author: Diedrich Vorberg <diedrich@tux4web.de>, May 2006
"""


# Python
import sys
from types import *
from string import *

# orm
from orm2 import sql
from orm2.datatypes import *

class serial(integer):
    """
    Datatype for automatically gernerated ids.
    
    From U{The FireBird FAQ <http://firebird.sourceforge.net/index.php?op=faq#q0011.dat>}
    
    How can i make an auto-incrementing primary key column? and is the NOT NULL constraint mandatory for a primary key?
    ===================================================================================================================
       In Firebird, you achieve an auto-incrementing PK using a generator
       and a BEFORE INSERT trigger::

          CREATE GENERATOR GEN_PK_ATABLE;
          COMMIT;

       Define the column, e.g., ATABLE_ID, as BIGINT or INTEGER and yes,
       the NOT NULL constraint is mandatory for a primary key.

       The trigger for automatic population of the key is this::

          CREATE TRIGGER BI_ATABLE FOR ATABLE
          ACTIVE BEFORE INSERT
          AS
          BEGIN
            IF(NEW.ATABLE_ID IS NULL) THEN 
            NEW.ATABLE_ID = GEN_ID(GEN_PK_ATABLE, 1);
          END

       I{This is B{NOT} what orm does! It does...}
       
    How can I get the value of my generated primary key after an insert ?
    =====================================================================
       Firebird doesn't currently return values from insert statements
       and, in multi-user, it isn't safe to query the generator
       afterwards (GEN_ID(Generator_name, 0) because you have no way
       to know whether the current 'latest' value was yours or someone
       else's. The trick is to get the generator value into your
       application as a variable before you post your insert. This
       way, you make it available not just for your insert but for any
       dependent rows you need to create for it inside the same
       transaction::
    
          SELECT GEN_ID(Generator_name, 1) AS MyVar FROM RDB$DATABASE;
    
       Some data access interfaces and drivers provide ways to do this
       automatically for you. For example, IB Objects implements the
       GeneratorLinks property for statement classes.


    How it is handeld by orm
    ========================    
       orm is the kind of interface that does this automatically for
       you. For any serial (and in fact L{common_serial
       <orm2.datatypes.common_serial>}, see above) column it will query
       the corresponding sequence and store the resulting value in the
       right attribute to be used in the INSERT statement. If you use
       a serial as your primary key, the select_after_insert()
       mechanism (see L{orm2.datasource.datasource}) will work
       correctly.
       
    """
    
    def __init__(self, column=None, sequence=None, title=None,
                 validators=(), widget_specs=()):
        """
        @param sequence: Either a string or a sql.identifyer instance,
           naming the sequence to be used by this serial column. Defaults
           to GEN_PK_<relation name>
        """
        integer.__init__(self, column, title, validators, widget_specs,
                         has_default=True)

        self.sequence = sequence

    def __init_dbclass__(self, dbclass, attribute_name):
        integer.__init_dbclass__(self, dbclass, attribute_name)

        if self.sequence is None:
            self.sequence = "GEN_PK_%s" % upper(dbclass.__relation__.name)

        if type(self.sequence) == StringType:
            self.sequence = sql.identifyer(self.sequence)
    
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
