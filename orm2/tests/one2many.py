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
# $Log: one2many.py,v $
# Revision 1.5  2006/05/02 13:34:42  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.4  2006/04/23 15:40:56  diedrich
# Set debugging output to False
#
# Revision 1.3  2006/04/15 23:27:53  diedrich
# *** empty log message ***
#
# Revision 1.2  2006/02/25 18:08:02  diedrich
# Made the many2one work with multi column keys.
#
# Revision 1.1  2006/01/01 20:37:48  diedrich
# Initial comit (half way into many2many)
#
#
#

"""
"""

import os, unittest

from orm2.debug import sqllog
# sqllog.verbose = True

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.relationships import *
from orm2 import sql

from orm2.datasource import datasource


# Model
class country(dbobject):
    id = common_serial()
    name = Unicode()

class city(dbobject):
    id = common_serial()
    name = Unicode()
    country_id = integer()

country.cities = one2many(city)
city.country = many2one(country)

class country_test(unittest.TestCase):

    data = ( ( "Germany", ("Witten", "Berlin", "Hamburg", u"München",), ),
             ( "USA", ("Washington", "New York", "Los Angeles",
                       "Winona",), ),
             ( "Great Britan", ("London", "Manchester", "Leeds",),),)

    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("CREATE TABLE country (id INTEGER, name VARCHAR)")
        self.ds.execute("""CREATE TABLE city (
                             id INTEGER,
                             name VARCHAR,
                             country_id INTEGER
                           )""")
    
    def test(self):
        for country_name, cities in self.data:
            new_country = country( name = country_name )
            
            self.ds.insert(new_country)
            
            for city_name in cities:
                new_country.cities.append( city(name=city_name) )

        new_country.cities.append( city(name="Bremen") )

        # But Bremen is not an English town, is it?
        result = self.ds.select(city, sql.where("name=",
                                                sql.string_literal("Bremen"))) 
        bremen = result.next()
        
        result = self.ds.select(country, sql.where("name=",
                                                sql.string_literal("Germany")))
        germany = result.next()

        # this will update the foreign key in the city table
        bremen.country_id = germany.id
        self.ds.flush_updates()

        german_cities = germany.cities.select(sql.order_by("name"))
        names = map(lambda c: c.name, list(german_cities))
        self.assertEqual(names, [u"Berlin", u"Bremen", u"Hamburg",
                                 u"München", u"Witten"])


        bremen_where = sql.where("name='Bremen'")
        self.assertEqual(len(germany.cities), 5)
        self.assertEqual(germany.cities.len(bremen_where), 1)

        bremen = germany.cities.select(bremen_where).next()
        self.assertEqual(bremen.name, u"Bremen")

    def tearDown(self):
        # Check if all the cities are in the right countries, ignore Bremen
        # doing so.
        pass
        
class country_test_pgsql(country_test):

    def setUp(self):
        # ORMTEST_PGSQL_CONN="adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))
        
        self.ds.execute("""CREATE TABLE country (
                             id SERIAL PRIMARY KEY,
                             name TEXT
                           )""")
        
        self.ds.execute("""CREATE TABLE city (
                             id SERIAL,
                             name TEXT,
                             country_id INTEGER REFERENCES country
                           )""")

class country_test_mysql(country_test):

    def setUp(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS country")
        self.ds.execute("DROP TABLE IF EXISTS city")
        
        self.ds.execute("""CREATE TABLE country (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                                      PRIMARY KEY(id),
                             name TEXT
                           )""")
        
        self.ds.execute("""CREATE TABLE city (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                                      PRIMARY KEY(id),
                             name TEXT,
                             country_id INTEGER REFERENCES country
                           )""")


# The example below tests two things: The many2one relationship and
# using non-integer, non-default foreign keys.

# This example made me want to implement multiple-column primary
# keys. The problem is, it's just too complicated. (Or is it...
# See one2many_mult.py ;-)

class domain(dbobject):
    id = common_serial()
    fqdn = text()

class email(dbobject):
    id = common_serial()
    local_part = text()
    remote_part = text()
    domain = many2one(domain, child_key="fqdn", foreign_key="remote_part", )

domain.emails = one2many(email, child_key="remote_part",
                         foreign_key="fqdn")

class domain_and_email_test(unittest.TestCase):
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("CREATE TABLE domain ( id INTEGER, fqdn VARCHAR )")
        self.ds.execute("""CREATE TABLE email (
                             id INTEGER,
                             local_part VARCHAR,
                             remote_part VARCHAR
                           )""")

    data = ( ("tux4web.de", ("info", "support", "diedrich", "spam"),),
             ("apple.com", ("steve", "store", "webmaster",),),)

    def test(self):
        for fqdn, emails in self.data:
            new_domain = domain(fqdn=fqdn)
            self.ds.insert(new_domain)

            for addr in emails:
                new_domain.emails.append(
                    email(remote_part=new_domain, local_part=addr))

        # Let's check...
        tux4web = self.ds.select_one(domain, sql.where("fqdn='tux4web.de'"))
        self.assertEqual(len(tux4web.emails), 4)

        apple = self.ds.select_by_primary_key(domain, 2)
        self.assertEqual(len(apple.emails), 3)

        result = apple.emails.select(sql.where("local_part = 'steve'"))
        steve = result.next()

        self.assertEqual(steve.local_part, "steve")
        self.assertEqual(steve.remote_part, "apple.com")

        # The other way 'round
        emails = self.ds.select(email)

        # This will yield one select statement for each email.
        # This effect can be prevented by using SQL joins.
        # This is been worked uppon.
        for a in emails:
            self.assertEqual(a.remote_part, a.domain.fqdn)


        new_email = email(local_part="dv")
        tux4web.emails.append(new_email)
        self.assertEqual(len(tux4web.emails), 5)
        
        result = tux4web.emails.select(sql.order_by("local_part"))
        result = list(result)
        last = result[-1]
        self.assertEqual(last.local_part, "support")

class domain_and_email_test_pgsql(domain_and_email_test):
    def setUp(self):
        # ORMTEST_PGSQL_CONN = "adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))
        
        self.ds.execute("""CREATE TABLE domain (
                             id SERIAL PRIMARY KEY,
                             fqdn TEXT UNIQUE
                           )""")
        
        self.ds.execute("""CREATE TABLE email (
                             id SERIAL PRIMARY KEY,
                             local_part TEXT,
                             remote_part TEXT REFERENCES domain(fqdn)
                           )""")

class domain_and_email_test_mysql(domain_and_email_test):
    def setUp(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS domain")
        self.ds.execute("DROP TABLE IF EXISTS email")
        
        self.ds.execute("""CREATE TABLE domain (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                  PRIMARY KEY(id),
                             fqdn VARCHAR(100) UNIQUE
                           )""")
        
        self.ds.execute("""CREATE TABLE email (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                  PRIMARY KEY(id),
                             local_part TEXT,
                             remote_part TEXT REFERENCES domain(fqdn)
                           )""")

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(country_test))
    suite.addTest(unittest.makeSuite(domain_and_email_test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(country_test_pgsql))
        suite.addTest(unittest.makeSuite(domain_and_email_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(country_test_mysql))
        suite.addTest(unittest.makeSuite(domain_and_email_test_mysql))

    unittest.TextTestRunner(verbosity=2).run(suite)
   
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

