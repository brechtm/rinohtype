#/usr/bin/env python
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
# $Log: many2one.py,v $
# Revision 1.2  2006/05/02 13:34:42  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.1  2006/04/28 08:34:02  diedrich
# Initial commit.
#
#
#

"""
"""

import os, unittest

from orm2.debug import sqllog
sqllog.buffer_size = 1
# sqllog.verbose = True

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.relationships import *
from orm2 import sql

from orm2.datasource import datasource


# Model Single Column Foreign Key
class item(dbobject):
    id = common_serial()
    title = text()

class item_category(dbobject):
    id = common_serial()
    name = text()

item.category = many2one(item_category)


# Model Multiple Column Foreign Key
class domain(dbobject):
    __primary_key__ = ( "name", "tld", )

    name = varchar(256)
    tld = varchar(8) # I may regret the 8 ;-)

class webserver(dbobject):
    id = common_serial()
    
    ip_address = text()

    domain_name = varchar(256)
    domain_tld = varchar(8)
    domain = many2one(domain,
                      child_key = ( "name", "tld", ), # key in the child table
                      foreign_key = ("domain_name",
                                     "domain_tld", ), # same thing here
                      cache=False)


class test(unittest.TestCase):

    def connect(self):
        self.ds = datasource("adapter=gadfly")


    def create_tables(self):

        self.ds.execute("""CREATE TABLE domain (
                              name VARCHAR,
                              tld VARCHAR
                           )""")

        self.ds.execute("""CREATE TABLE webserver (
                              id INTEGER,
                              ip_address VARCHAR,

                              domain_name VARCHAR,
                              domain_tld VARCHAR
                           )""")   
        
        self.ds.execute("""CREATE TABLE item (
                              id INTEGER,
                              title VARCHAR,
                              item_category_id INTEGER 
                           )""")
        
        self.ds.execute("""CREATE TABLE item_category (
                              id INTEGER,
                              name VARCHAR
                           )""")


    def setUp(self):
        self.connect()
        self.create_tables()

        self.ds.insert(item_category(name="Category One"))
        self.ds.insert(item_category(name="Category Two"))
        self.ds.insert(item_category(name="Category Three"))


        self.ds.insert(domain(name="tux4web", tld="de"))
        self.ds.insert(domain(name="t4w", tld="de"))
        self.ds.insert(domain(name="superstyler", tld="de"))
        self.ds.insert(domain(name="apple", tld="com"))
        

    def test_single_key_no_null(self):
        """
        Since gadfly doesn't suppert NULL values the tests have to be in
        two parts: tests for gadfly, tests for 'grown up' (no offense) RDBMS
        """
        category_one = self.ds.select_by_primary_key(item_category, 1)
        category_two = self.ds.select_by_primary_key(item_category, 2)
        category_three = self.ds.select_by_primary_key(item_category, 3)

        # The most simple case...
        item_one = item(title="Item One", category=category_three)
        self.ds.insert(item_one)
        # self.assertEqual(sqllog.queries[-1], "INSERT INTO item(item_category_id, title, id) VALUES (3, 'Item One', 1)")
        self.assertEqual(item_one.category.name, "Category Three")
        
        item_one.category = category_one
        self.assertEqual(item_one.category.name, "Category One")

        self.ds.flush_updates()
        self.assertEqual(sqllog.queries[-1],
                         "UPDATE item SET item_category_id = 1 WHERE id = 1")

    def test_multiple_key_no_null(self):
        tux4web = self.ds.select_by_primary_key(domain, ("tux4web", "de",))
        t4w = self.ds.select_by_primary_key(domain, ("t4w", "de",))

        ws = webserver(ip_address="10.0.0.1", domain=tux4web)
        self.ds.insert(ws)

        # self.assertEqual(sqllog.queries[-1], "INSERT INTO webserver(domain_name, id, ip_address, domain_tld) VALUES ('tux4web', 1, '10.0.0.1', 'de')")
        self.assertEqual(ws.domain, tux4web)

        ws.domain = t4w
        self.ds.flush_updates()

        self.assertEqual(ws.domain, t4w)


    def tearDown(self):
        self.ds.close()

class test_grown_up(test):
    def test_single_key(self):
        category_one = self.ds.select_by_primary_key(item_category, 1)
        category_two = self.ds.select_by_primary_key(item_category, 2)
        category_three = self.ds.select_by_primary_key(item_category, 3)

        # The most simple case...
        item_one = item(title="Item One")
        self.ds.insert(item_one)

        item_one.category = category_one
        self.assertEqual(item_one.category, category_one)

        item_one.category = category_two
        self.assertEqual(item_one.category, category_two)


    def test_multiple_key_no_null(self):
        tux4web = self.ds.select_by_primary_key(domain, ("tux4web", "de",))
        t4w = self.ds.select_by_primary_key(domain, ("t4w", "de",))

        ws = webserver(ip_address="10.0.0.1")
        self.ds.insert(ws)

        ws.domain = tux4web
        self.assertEqual(ws.domain, tux4web)

        ws.domain = t4w
        self.ds.flush_updates()

        self.assertEqual(ws.domain, t4w)

class test_pgsql(test_grown_up):
    def connect(self):
        # ORMTEST_PGSQL_CONN="adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))
        

    def create_tables(self):

        self.ds.execute("""CREATE TABLE domain (
                              name TEXT,
                              tld TEXT,

                              PRIMARY KEY(name, tld)
                           )""")

        self.ds.execute("""CREATE TABLE webserver (
                              id SERIAL, PRIMARY KEY(id),
                              ip_address VARCHAR NOT NULL,

                              domain_name VARCHAR,
                              domain_tld VARCHAR,

                              FOREIGN KEY (domain_name, domain_tld)
                                       REFERENCES domain(name, tld)
                           )""")   
        
        self.ds.execute("""CREATE TABLE item_category (
                              id SERIAL, PRIMARY KEY(id),
                              name TEXT
                           )""")

        self.ds.execute("""CREATE TABLE item (
                              id SERIAL, PRIMARY KEY(id),
                              title VARCHAR,
                              item_category_id INTEGER,

                              FOREIGN KEY (item_category_id)
                                        REFERENCES item_category
                           )""")
        

class test_mysql(test_grown_up):
    def connect(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        
    def create_tables(self):
        self.ds.execute("DROP TABLE IF EXISTS domain")
        self.ds.execute("""CREATE TABLE domain (
                              name VARCHAR(255),
                              tld VARCHAR(19),

                              PRIMARY KEY(name, tld)
                           )""")

        self.ds.execute("DROP TABLE IF EXISTS webserver")
        self.ds.execute("""CREATE TABLE webserver (
                              id INTEGER NOT NULL AUTO_INCREMENT,
                                                       PRIMARY KEY(id),
                              ip_address VARCHAR(100) NOT NULL,

                              domain_name VARCHAR(255),
                              domain_tld VARCHAR(10),

                              FOREIGN KEY (domain_name, domain_tld)
                                       REFERENCES domain(name, tld)
                           )""")   
        
        self.ds.execute("DROP TABLE IF EXISTS item_category")
        self.ds.execute("""CREATE TABLE item_category (
                              id INTEGER NOT NULL AUTO_INCREMENT,
                                                       PRIMARY KEY(id),
                              name TEXT
                           )""")

        self.ds.execute("DROP TABLE IF EXISTS item")
        self.ds.execute("""CREATE TABLE item (
                              id INTEGER NOT NULL AUTO_INCREMENT,
                                                       PRIMARY KEY(id),
                              title VARCHAR(255),
                              item_category_id INTEGER,

                              FOREIGN KEY (item_category_id)
                                        REFERENCES item_category
                           )""")
        

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(test_mysql))

    unittest.TextTestRunner(verbosity=2).run(suite)
