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
# $Log: inheritance.py,v $
# Revision 1.3  2006/04/23 15:39:15  diedrich
# Changed varchar to string column, because varchar now has a
# length_check validator
#
# Revision 1.2  2006/01/01 20:49:07  diedrich
# Changed from test adapter to gadfly.
#
# Revision 1.1  2005/12/18 22:33:43  diedrich
# Initial commit
#
#

"""
Test the inheritance mechanism for dbclasses.
"""

import os, unittest

from orm2.debug import sqllog
sqllog.buffer_size = 10

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource

class vehicle(dbobject):
    id = integer()
    name = string()
    
class ship(vehicle):
    replacement = integer()

class steam_ship(ship):
    smokestacks = integer()

def property_names(dbobj):
    properties = dbobj.__dbproperties__()
    ret = map(lambda p: p.attribute_name, properties)
    ret.sort()
    return tuple(ret)

def IN(seq0, seq1):
    for item in seq0:
        if item not in seq1:
            return False

    return True

class inheritance(unittest.TestCase):
    def setUp(self):
        ds = datasource("adapter=gadfly")
        
    def test_simple(self):
        self.assertEqual(property_names(vehicle(id=1, name="Vehicle 0")),
                         ( "id", "name", ))
        
        self.assert_( IN( ( "id", "name", ), vehicle.__dict__.keys(), ))
        
        self.assert_( IN( ( "id", "name", "replacement", ),
                          ship.__dict__.keys(), ))
        
        self.assert_( IN( ( "id", "name", "replacement", "smokestacks"),
                          steam_ship.__dict__.keys(), ))

        self.assertEqual(property_names(vehicle(id=2, name="Herbie")),
                         ( "id", "name", ))

        self.assertEqual(property_names(ship(id=3, name="Enterprise",
                                             replacement=1000)),
                                        ( "id", "name", "replacement", ))

        self.assertEqual(property_names(steam_ship(id=3, name="Titanic",
                                                   replacement=1000,
                                                   smokestacks=4)),
                                        ( "id", "name", "replacement",
                                          "smokestacks", ))

if __name__ == '__main__':
    unittest.main()
        
    
