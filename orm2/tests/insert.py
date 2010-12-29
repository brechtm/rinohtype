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
# $Log: insert.py,v $
# Revision 1.6  2006/09/04 15:59:41  diedrich
# Change unicode characters used in test.
#
# Revision 1.5  2006/05/10 21:56:13  diedrich
# Added tests for firebird adapter
#
# Revision 1.4  2006/05/02 13:34:43  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.3  2006/01/01 20:49:47  diedrich
# Changed from test adapter to gadfly. Also changed numerous things that
# came up during development.
#
# Revision 1.2  2005/12/31 10:12:31  diedrich
# Use one datamodel for all tests.
#
# Revision 1.1  2005/12/18 22:33:44  diedrich
# Initial commit
#
#

"""
This module will create a single object/row and insert into a database.
To run the default test you'll have to install the gadfly module.
See README.txt
"""

import os, unittest

from orm2.debug import sqllog
sqllog.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource

class person(dbobject):
    """
    This is our minimal data model consiting of one class
    """
    __relation__ = "person"
    
    id = common_serial()
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
                             id INTEGER,
                             firstname VARCHAR,
                             lastname VARCHAR,
                             height INTEGER ) """, modify=True)
        
    def test_simple(self):
        sample = person(firstname = u"Diedrich üäöÜÄÖß",
			lastname = u"Vorberg «®øåº",
			height = 186)

        self.ds.insert(sample)
        self.sample = sample

    def tearDown(self):
        self.assertEqual(self.sample.id, 1)
        
        result = self.ds.select(person)
        result = list(result)
        
        self.assert_(len(result) == 1)

        me = result[0]
        self.assertEqual(me.firstname, u"Diedrich üäöÜÄÖß")
        self.assertEqual(me.lastname, u"Vorberg «®øåº")
        self.assertEqual(me.height, 186)
        
class person_insert_test_pgsql(person_insert_test):

    def setUp(self):
        # ORMTEST_PGSQL_CONN="adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))
        self.ds.execute("""CREATE TABLE person (
                             id SERIAL,
                             firstname TEXT,
                             lastname TEXT,
                             height INTEGER ) """, modify=True)
        

class person_insert_test_mysql(person_insert_test):

    def setUp(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))
        self.ds.execute("DROP TABLE IF EXISTS person")
        self.ds.execute("""CREATE TABLE person (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                                       PRIMARY KEY(id),
                             firstname TEXT,
                             lastname TEXT,
                             height INTEGER ) """, modify=True)
        
class person_insert_test_firebird(person_insert_test):
    def setUp(self):
        # ORMTEST_FIREBIRD_CONN="adapter=firebird dsn=localhost:/tmp/test user=sysdba password=masterkey"
        self.ds = datasource(os.getenv("ORMTEST_FIREBIRD_CONN"))

        self.ds.execute("""RECREATE TABLE person (
                             id INTEGER NOT NULL, PRIMARY KEY(id),
                             firstname VARCHAR(100),
                             lastname VARCHAR(100),
                             height INTEGER
                           )""", modify=True)
        self.ds.commit()

        try:
            self.ds.execute("DROP GENERATOR GEN_PK_PERSON", modify=True)
        except:
            pass
        
        self.ds.execute("CREATE GENERATOR GEN_PK_PERSON", modify=True)
        self.ds.commit()
    


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(person_insert_test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_test_mysql))

    if os.environ.has_key("ORMTEST_FIREBIRD_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_test_firebird))
        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

