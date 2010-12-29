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
# $Log: pickle.py,v $
# Revision 1.1  2006/05/13 14:56:56  diedrich
# Initial commit
#
#
#

"""
This module tests the L{orm2.util.datatypes.pickle} datatype.
"""

import os, unittest

from orm2.debug import sqllog
# sqllog.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2.util.datatypes import pickle

class person(dbobject):
    """
    This is our minimal data model consiting of one class
    """
    __relation__ = "person"
    
    id = common_serial()
    firstname = Unicode()
    lastname = Unicode()
    attributes = pickle()
    
class person_insert_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    """
    
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE person (
                             id INTEGER,
                             firstname VARCHAR,
                             lastname VARCHAR,
                             attributes VARCHAR ) """, modify=True)
        
    def test_simple(self):
        sample = person(firstname = u"Diedrich",
			lastname = u"Vorberg",
                        attributes={"height": 186,
                                    "weight": 'Too much',
                                    "age": 28.75})

        self.ds.insert(sample)
        self.sample = sample

        self.assertEqual(self.sample.id, 1)
        
        result = self.ds.select(person)
        result = list(result)
        
        self.assert_(len(result) == 1)
        me = result[0]

        self.assertEqual(me.attributes["height"], 186)
        self.assertEqual(me.attributes["age"], 28.75)

        


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(person_insert_test))

        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

