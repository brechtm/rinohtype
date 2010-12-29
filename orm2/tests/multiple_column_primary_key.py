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
# $Log: multiple_column_primary_key.py,v $
# Revision 1.3  2006/05/02 13:34:42  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.2  2006/04/28 08:46:36  diedrich
# Changed my hight. (Size does matter!?!)
#
# Revision 1.1  2006/02/25 18:06:54  diedrich
# Initial commit.
#
#
#

"""
This is an enhanced version of the person example that tests orm2's
ability to use multi column primary keys.
"""

import os, unittest

from orm2.debug import sqllog
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource

class person(dbobject):
    """
    This is our minimal data model consiting of one class
    """
    __primary_key__ = ( "firstname", "lastname", )
    
    firstname = Unicode()
    lastname = Unicode()
    height = integer()
    
class person_insert_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    """
    
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE person (
                             firstname VARCHAR,
                             lastname VARCHAR,
                             height INTEGER ) """, modify=True)
        
    def test_simple(self):
        sample = person(firstname = u"Diedrich",
			lastname = u"Vorberg",
			height = 186)

        self.ds.insert(sample)
        # self.sample = sample

        self.assertEqual(sample.firstname, "Diedrich")

        # get the result from the database
        result = self.ds.select(person)
        result = list(result)
        
        self.assert_(len(result) == 1)

        me = result[0]
        self.assertEqual(me.firstname, u"Diedrich")
        self.assertEqual(me.lastname, u"Vorberg")
        self.assertEqual(me.height, 186)

        # let's try an update
        me.height = 187 # grew some more hair ;-)
        self.ds.flush_updates()

        self.assertEqual(sqllog.queries[-1],
                         "UPDATE person SET height = 187 WHERE firstname = 'Diedrich' AND lastname = 'Vorberg'")
        
class person_insert_test_pgsql(person_insert_test):

    def setUp(self):
        # ORMTEST_PGSQL_CONN = "adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))
        self.ds.execute("""CREATE TABLE person (
                             firstname TEXT,
                             lastname TEXT,
                             height INTEGER,
                             PRIMARY KEY(firstname, lastname)
                           ) """, modify=True)
        
class person_insert_test_mysql(person_insert_test):

    def setUp(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))
        self.ds.execute("DROP TABLE IF EXISTS person", modify=True)
        self.ds.execute("""CREATE TABLE person (
                             firstname VARCHAR(100), -- MySQL needs to know
                             lastname VARCHAR(100),  -- the key length
                             height INTEGER,
                             PRIMARY KEY(firstname, lastname)
                           ) """, modify=True)
        

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(person_insert_test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_test_mysql))

    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

