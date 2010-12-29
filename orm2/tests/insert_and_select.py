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
# $Log: insert_and_select.py,v $
# Revision 1.6  2006/09/05 16:54:00  diedrich
# Of course, Python's database API doesn't support ? as a placeholder
# but %s. This also means that all %s must be escaped in input SQL. This
# remains untested for firebird.
#
# Revision 1.5  2006/05/10 21:56:13  diedrich
# Added tests for firebird adapter
#
# Revision 1.4  2006/05/02 13:34:42  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.3  2006/04/23 15:40:07  diedrich
# Added a test for updates on a dbobj that has been retrieved from the
# database rather than newly created. This was not tested previously.
#
# Revision 1.2  2006/02/25 18:08:45  diedrich
# Fixed small bug
#
# Revision 1.1  2006/01/01 20:37:48  diedrich
# Initial comit (half way into many2many)
#
#
#

"""
Insert a couple of different objects into a couple of different tables and
retrieve them or part of them.
"""

import os, unittest, struct, socket
from types import *

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2 import sql
from orm2.debug import sqllog
# sqllog.verbose = True


def same_data(l1, l2):
    if len(l1) == 0 or len(l2) == 0:
        return False
    
    for a in l1:
        if a not in l2:
            return False

    return True

class person(dbobject):
    """
    From the insert.py test...
    """
    id = common_serial()
    firstname = Unicode()
    lastname = Unicode()
    height = integer()
    gender = char(2)

class person_insert_and_select_test(unittest.TestCase):
    """
    Test case that runs on the gadfly adapter.
    The gadfly adapter doesn't know NULL values and Unicode screws it up.
    So the jucyer tests are reserved for the 'real' databases.
    """

    sample_data = ( (u"Diedrich", u"Vorberg", 186, "m"),
                    (u"Marie-Luise", u"Vorberg", 174, "f"),
                    (u"Annette", u"Vorberg", 168, "f"), )

    def connect_and_create_table(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE person (
                             id INTEGER,
                             firstname VARCHAR,
                             lastname VARCHAR,
                             height INTEGER,
                             gender VARCHAR) """, modify=True)
    
    def setUp(self):
        self.connect_and_create_table()
        
        for firstname, lastname, height, gender in self.sample_data:
            dbobj = person(firstname = firstname,
                           lastname = lastname,
                           height = height,
                           gender = gender)
            self.ds.insert(dbobj)

    def insert_unicode_person(self):
        unicode_person = person(firstname = u"% üäöÜÄÖß",
                                lastname = u"«€®øåœ±çv")
        self.ds.insert(unicode_person)

    def tearDown(self):
        self.ds.execute("DROP TABLE person")


    def test(self):
        self.select_all()
        self.select_with_where()
        
    def select_all(self):
        all = self.ds.select(person)

        tpls = []
        for dbobj in all:
            tpls.append( (dbobj.firstname, dbobj.lastname,
                          dbobj.height, dbobj.gender,) )

        self.assert_(same_data(self.sample_data, tpls))

    def select_with_where(self):
        result = self.ds.select(person, sql.where("height > 170"))
        
        firstnames = map(lambda p: p.firstname, list(result))
        firstnames.sort()
        
        self.assertEqual( firstnames, [ u"Diedrich", u"Marie-Luise", ] )


    def select_with_where_and_order_by(self):
        result = self.ds.select(person,
                                sql.where("height IS NOT NULL"),
                                sql.order_by("height"))
        
        firstnames = map(lambda p: p.firstname, list(result))
        self.assertEqual(firstnames, [u"Annette", u"Marie-Luise",
                                      u"Diedrich", ])

    def select_unicode(self):
        result = self.ds.select(person, sql.where("height IS NULL"))
        unicode_person = list(result)[0]
        self.assertEqual(unicode_person.firstname, u"% üäöÜÄÖß")

    def select_and_set(self):
        result = self.ds.select(person, sql.where("height > 170"))

        for person in result:
            person.height += 10

        self.ds.flush_updates()

        
class person_insert_and_select_test_pgsql(person_insert_and_select_test):

    def connect_and_create_table(self):
        # ORMTEST_PGSQL_CONN = "adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))
        self.ds.execute("""CREATE TABLE person (
                             id SERIAL,
                             firstname TEXT,
                             lastname TEXT,
                             height INTEGER,
                             gender CHAR(1)) """, modify=True)
        
        self.insert_unicode_person()
        
    def test(self):
        self.select_all()
        self.select_with_where()
        self.select_with_where_and_order_by()
        self.select_unicode()
        
        
class person_insert_and_select_test_mysql(person_insert_and_select_test):

    def connect_and_create_table(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS person", modify=True)
        self.ds.execute("""CREATE TABLE person (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                   PRIMARY KEY(id),
                             firstname TEXT,
                             lastname TEXT,
                             height INTEGER,
                             gender CHAR(1)) """, modify=True)
        
        # self.insert_unicode_person()
        
    def test(self):
        self.select_all()
        self.select_with_where()
        self.select_with_where_and_order_by()
        self.select_unicode()
        
        
class person_insert_and_select_test_firebird(person_insert_and_select_test):

    def connect_and_create_table(self):
        # ORMTEST_FIREBIRD_CONN="adapter=firebird dsn=localhost:/tmp/test user=sysdba password=masterkey"

        self.ds = datasource(os.getenv("ORMTEST_FIREBIRD_CONN"))

        self.ds.execute("""RECREATE TABLE person (
                             id INTEGER NOT NULL, PRIMARY KEY(id),
                             firstname VARCHAR(100),
                             lastname VARCHAR(100),
                             height INTEGER,
                             gender CHAR(1)) """, modify=True)
        
        try:
            self.ds.execute("DROP GENERATOR GEN_PK_PERSON", modify=True)
        except:
            pass
        
        self.ds.execute("CREATE GENERATOR GEN_PK_PERSON", modify=True)
        self.ds.commit()
        
        self.insert_unicode_person()
        
    def test(self):
        self.select_all()
        self.select_with_where()
        self.select_with_where_and_order_by()
        self.select_unicode()
        

######################################################################

# The code that does the actual conversion is from
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66517
# by Alex Martelli and Greg Jorgensen. See pgsql's Internet Address
# datatypes (which are not yet written...) Anyway, the old orm version
# contained basically the same code.

def dottedQuadToNum(ip): 
    "convert decimal dotted quad string to long integer"
    return struct.unpack('L',socket.inet_aton(ip))[0]

def numToDottedQuad(n):
    "convert long int to dotted quad string"
    return socket.inet_ntoa(struct.pack('L',n))


class dotted_quad(Long):
    """
    dotted_quad accepts to kinds of values: Strings representing IP
    addresses or long doing the same (see __set__() below).
    It will only return strings (see __get__() below).
    """    
    def __convert__(self, value):
        if type(value) == StringType:
            return dottedQuadToNum(value)
        else:
            raise AttributeError("dotted_quad properties must be set to string values")

    def __set_from_result__(self, ds, dbobj, value):
        # We know that value is of integer or long type, no need to test
        # it.
        setattr(dbobj, self.data_attribute_name(), value)
    
    def __get__(self, dbobj, owner=None):
        i = Long.__get__(self, dbobj, owner)
        return numToDottedQuad(i)

class host(dbobject):
    """
    Represent a host on the internet by its ip address.

    the ip_numeric and ip_dotted_quad properties point to the same SQL column.
    """
    id = common_serial()
    fqhn = text()
    ip_numeric = Long(column = "ip")
    ip_dotted_quad = dotted_quad(column = "ip")

class host_insert_and_select_test(unittest.TestCase):
    """
    This test case is ment to test dbobject's feature that one
    table column may have several representations as properties
    in a dbclass. This is particularly usefull when using relationships:
    a foreign key may be represented by a many2one relationship (representing
    the referred object) and an integer (representing the actual foreign key)
    at the same time.

    Here I will use a column which is represented as a Unicode string and a
    binary representation in the backend's encoding (utf-8 probably)
    at the same time.

    To create even a half-way sensible example and to test another of orm's
    features I created a custom datatype that will represent an unsigned
    integer in the database as an IP address in dotted quod notation.
    """

    sample_data = ( ("localhost", "127.0.0.1",),
                    ("lisa.tux4web.de", "192.168.2.1",),
                    ("bart.tux4web.de", "192.168.2.2",), )

    def connect_and_create_table(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE host (
                             id INTEGER,
                             fqhn VARCHAR,
                             ip INTEGER) """, modify=True)
    
    def setUp(self):
        self.connect_and_create_table()
        
        for name, ip in self.sample_data:
            dbobj = host(fqhn = name, ip_dotted_quad = ip)
            self.ds.insert(dbobj)

    def tearDown(self):
        self.ds.execute("DROP TABLE host")

    def test(self):
        localhost = self.ds.select_one(host, sql.where("fqhn = 'localhost'"))
        self.assertEqual(localhost.ip_numeric, dottedQuadToNum("127.0.0.1"))
        self.assertEqual(localhost.ip_dotted_quad, "127.0.0.1")

        lisa = self.ds.select_one(host, sql.where("fqhn = 'lisa.tux4web.de'"))
        lisa.ip_numeric = 0L
        self.ds.flush_updates()
        self.assertEqual(lisa.ip_numeric, 0L)
        self.assertEqual(lisa.ip_dotted_quad, "0.0.0.0")
        
        bart = self.ds.select_one(host, sql.where("fqhn = 'bart.tux4web.de'"))
        bart.ip_dotted_quad = "255.255.255.255"
        self.ds.flush_updates()
        self.assertEqual(bart.ip_numeric, dottedQuadToNum("255.255.255.255"))
        self.assertEqual(bart.ip_dotted_quad, "255.255.255.255")
        

class host_insert_and_select_test_pgsql(unittest.TestCase):
    def connect_and_create_table(self):
        # ORMTEST_PGSQL_CONN = "adapter=pgsql host=localhost"
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))

        self.ds.execute("""CREATE TABLE host (
                             id SERIAL,
                             fqhn TEXT,
                             ip INTEGER) """, modify=True)


class host_insert_and_select_test_mysql(unittest.TestCase):
    def connect_and_create_table(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS host", modify=True)
        self.ds.execute("""CREATE TABLE host (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                   PRIMARY KEY(id),
                             fqhn TEXT,
                             ip INTEGER) """, modify=True)

class host_insert_and_select_test_firebird(unittest.TestCase):
    def connect_and_create_table(self):
        # ORMTEST_FIREBIRD_CONN="adapter=firebird dsn=localhost:/tmp/test user=sysdba password=masterkey"

        self.ds = datasource(os.getenv("ORMTEST_FIREBIRD_CONN"))

        self.ds.execute("""RECREATE TABLE host (
                             id INTEGER NOT NULL, PRIMARY KEY(id),
                             fqhn VARCHAR(100),
                             ip INTEGER) """, modify=True)

if __name__ == '__main__':

    # IP Number conversion does not seem to work with Python 2.4
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(person_insert_and_select_test))
    # suite.addTest(unittest.makeSuite(host_insert_and_select_test))
    
    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_and_select_test_pgsql))
        #suite.addTest(unittest.makeSuite(host_insert_and_select_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_and_select_test_mysql))
        #suite.addTest(unittest.makeSuite(host_insert_and_select_test_mysql))

    if os.environ.has_key("ORMTEST_FIREBIRD_CONN"):
        suite.addTest(unittest.makeSuite(person_insert_and_select_test_firebird))
        #suite.addTest(unittest.makeSuite(host_insert_and_select_test_firebird))
        
        
    unittest.TextTestRunner(verbosity=2).run(suite)


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

