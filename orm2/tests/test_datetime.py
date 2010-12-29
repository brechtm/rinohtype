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
# $Log: test_datetime.py,v $
# Revision 1.1  2006/07/03 17:08:32  diedrich
# Initial commit
#
#
#
#

"""
Insert a couple of different objects into a couple of different tables and
retrieve them or part of them.
"""

import os, unittest, struct, socket
from types import *
from datetime import datetime as py_datetime

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2 import sql
from orm2.debug import sqllog
sqllog.verbose = False
sqllog.buffer_size = 10

class datetest(dbobject):
    """
    From the insert.py test...
    """
    id = common_serial()
    dt = date()
    tm = time()
    dttm = datetime()

class datetime_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    The gadfly adapter doesn't know NULL values and Unicode screws it up.
    So the jucyer tests are reserved for the 'real' databases.
    """

    def setUp(self):
        self.connect_and_create_table()
        
    def test(self):
        dob = py_datetime(1977, 7, 19)
        five_past_noon = py_timedelta(hours=12, minutes=5)
        dttm = py_datetime(1977, 7, 19, 12, 5)
        
        d = datetest(dt=dob, tm=five_past_noon, dttm=dttm)
        
        self.ds.insert(d)
        self.assertEqual(sqllog.queries[-2],
                         "INSERT INTO datetest(tm, dttm, dt) VALUES ('12:05:00', '1977-07-19 12:05:00', '1977-07-19')")

        result = self.ds.select(datetest)
        first = result.next()

        self.assert_(first.dt == dob)
        self.assert_(first.tm == five_past_noon)
        self.assert_(first.dttm == dttm)

        
class datetime_test_pgsql(datetime_test):

    def connect_and_create_table(self):
        # ORMTEST_PGSQL_CONN = "adapter=pgsql host=localhostq"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))

        self.ds.execute("""CREATE TABLE datetest (
                             id SERIAL, PRIMARY KEY(id),
                             dt DATE,
                             tm TIME,
                             dttm TIMESTAMP
                             ) """, modify=True)
    

        
        
class datetime_test_mysql(datetime_test):

    def connect_and_create_table(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS datetest", modify=True)
        self.ds.execute("""CREATE TABLE datetest (
                             id SERIAL, PRIMARY KEY(id),
                             dt DATE,
                             tm TIME,
                             dttm TIMESTAMP
                             ) """, modify=True)
        
        
class datetime_test_firebird(datetime_test):

    def connect_and_create_table(self):
        # ORMTEST_FIREBIRD_CONN="adapter=firebird dsn=localhost:/tmp/test user=sysdba password=masterkey"

        self.ds = datasource(os.getenv("ORMTEST_FIREBIRD_CONN"))

        self.ds.execute("""RECREATE TABLE datetest (
                             id INTEGER NOT NULL, PRIMARY KEY(id),
                             dt DATE,
                             tm TIME,
                             dttm TIMESTAMP
                             ) """, modify=True)
        
        try:
            self.ds.execute("DROP GENERATOR GEN_PK_DATETEST", modify=True)
        except:
            pass
        
        self.ds.execute("CREATE GENERATOR GEN_PK_DATETEST", modify=True)
        self.ds.commit()
        
        

if __name__ == '__main__':
    suite = unittest.TestSuite()
    
    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(datetime_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(datetime_test_mysql))

    if os.environ.has_key("ORMTEST_FIREBIRD_CONN"):
        suite.addTest(unittest.makeSuite(datetime_test_firebird))
        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

