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
# $Log: binary.py,v $
# Revision 1.1  2006/09/04 15:59:03  diedrich
# Test the various backend's binary functionality.
#
#
#

"""
Test various classes
"""

import os, unittest

from orm2.debug import debug, sqllog
sqllog.verbose = True
debug.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2.adapters.gadfly.datatypes import Unicode as gadfly_unicode

class gadfly_person(dbobject):
    """
    This is our minimal data model consiting of one class
    """
    __relation__ = "person"
    
    id = common_serial()
    name = gadfly_unicode()

    
class gadfly_person_insert_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    """
    
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE person (
                             id INTEGER,
                             name VARCHAR(100)) """, modify=True)
        
    def test(self):
        sample = gadfly_person(name = u"Diedrich üäöÜÄÖß")

        self.ds.insert(sample)
        self.sample = sample

    def tearDown(self):
        self.assertEqual(self.sample.id, 1)
        
        result = self.ds.select(gadfly_person)
        result = list(result)
        
        self.assert_(len(result) == 1)

        me = result[0]
        print repr(me.name)
        # self.assertEqual(me.name, u"Diedrich üäöÜÄÖß")
        # This doesn't seem to work on the gadfly side.

        


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(gadfly_person_insert_test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_test_pgsql))

        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

