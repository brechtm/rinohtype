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
# $Log: firebird_serial.py,v $
# Revision 1.2  2006/05/11 20:43:09  diedrich
# Added more info on required environment variable
#
# Revision 1.1  2006/05/10 21:55:58  diedrich
# Initial commit
#
#

'''
This program will test the serial and common_serial mechanisms of the
firebird adapter. If requires an envionment variable called

   ORMTEST_FIREBIRD_CONN

to be set to an appropriate connection string. As for example:

   ORMTEST_FIREBIRD_CONN="adapter=firebird dsn=localhost:/tmp/test user=sysdba password=masterkey"
'''

import os, unittest

from orm2.debug import sqllog
# sqllog.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datasource import datasource
from orm2.datatypes import *
from orm2.adapters.firebird.datatypes import serial

# model

class test_with_serial(dbobject):
    __relation__ = "test"

    id = serial(sequence="gen_pk_test")
    s = varchar(100)

class test_with_common_serial(dbobject):
    __relation__ = "test"

    id = common_serial()
    s = varchar(100)



class serial_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    """
    
    def setUp(self):
        # ORMTEST_FIREBIRD_CONN="adapter=firebird dsn=localhost:/tmp/test user=sysdba password=masterkey"
        self.ds = datasource(os.getenv("ORMTEST_FIREBIRD_CONN"))

        self.ds.execute("""RECREATE TABLE test (
                             id INTEGER NOT NULL,
                             s VARCHAR(100),

                             PRIMARY KEY(id)
                           )""", modify=True)
        self.ds.commit()

        try:
            self.ds.execute("DROP GENERATOR GEN_PK_TEST", modify=True)
        except:
            pass
        
        self.ds.execute("CREATE GENERATOR GEN_PK_TEST", modify=True)
        self.ds.commit()
        

    def test(self):
        one = test_with_serial(s = "One")
        self.ds.insert(one)

        self.assertEqual(sqllog.queries[-1],
                         "INSERT INTO test(s, id) VALUES ('One', 1)")

        two = test_with_common_serial(s = "Two")
        self.ds.insert(two)

        self.assertEqual(sqllog.queries[-1],
                         "INSERT INTO test(s, id) VALUES ('Two', 2)")

    def tearDown(self):
        del self.ds

if __name__ == '__main__':
    suite = unittest.TestSuite()

    if os.environ.has_key("ORMTEST_FIREBIRD_CONN"):
        suite.addTest(unittest.makeSuite(serial_test))

    unittest.TextTestRunner(verbosity=2).run(suite)


