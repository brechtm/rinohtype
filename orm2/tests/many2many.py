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
# $Log: many2many.py,v $
# Revision 1.4  2006/05/02 13:34:42  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.3  2006/04/23 15:40:30  diedrich
# Set debugging output to False
#
# Revision 1.2  2006/04/15 23:21:47  diedrich
# Wrote the actual testing code
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
#sqllog.verbose = True
#sqllog.buffer_size = 10

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.relationships import *
from orm2 import sql

from orm2.datasource import datasource


# Model

class domain(dbobject):
    id = common_serial()
    fqdn = text()

class mail_admin(dbobject):
    id = common_serial()
    email = text()
    name = text()

domain.mail_admins = many2many(mail_admin, "domain_to_mail_admin")
mail_admin.domains = many2many.reverse(domain, "mail_admins")

# mail_admin.mail_servers = many2many(mail_server,
#                                     "mail_admin_to_mail_server",
#                                     parent_own_key = "email",
#                                     parent_link_column = "admin_email",
#                                     child_own_key = "fqhn",
#                                     child_link_column = "server_hostname")

# mail_server.mail_admins = many2many.reverse(mail_admin, "mail_servers")

class many2many_test(unittest.TestCase):
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE domain (
                             id INTEGER,
                             fqdn VARCHAR
                           )""")

        self.ds.execute("""CREATE TABLE mail_admin (
                             id INTEGER,
                             email VARCHAR,
                             name VARCHAR
                           )""")

        self.ds.execute("""CREATE TABLE mail_server (
                             id INTEGER,
                             fqhn VARCHAR
                           )""")

        self.ds.execute("""CREATE TABLE domain_to_mail_admin (
                             domain_id INTEGER,
                             mail_admin_id INTEGER
                           )""")

        self.ds.execute("""CREATE TABLE mail_admin_to_mail_server (
                             admin_email VARCHAR,
                             server_hostname VARCHAR
)""")



    def test(self):
        root = mail_admin(name="Me", email="diedrich@tux4web.de")
        one = mail_admin(name="Admin One", email="admin@one.com")
        two = mail_admin(name="Admin Two", email="admin@two.com")

        self.ds.insert(one)
        self.ds.insert(two)
        self.ds.insert(root)

        domains = []
        for a in ("tux4web.de", "t4w.de", "vorberg.name",):
            d = domain(fqdn=a)
            domains.append(d)
            self.ds.insert(d)

        # sqllog.reset()
            
        one.domains.append(domains[0])
        
        two.domains.append(domains[1])
        two.domains.append(domains[2])

        self.assertEqual(one.domains.len(), 1)
        self.assertEqual(two.domains.len(), 2)

        root.domains = domains

        self.assertEqual(len(root.domains), 3)

        root.domains.append(domain(fqdn="test.de"))

        self.assertEqual(len(root.domains), 4)

        # type checking...
        self.assertRaises(TypeError, root.domains.append, one)

        def invalid_set(): root.domains = 0
        self.assertRaises(ValueError, invalid_set)

        # some special cases:
        count = root.domains.len(sql.where("domain.fqdn = 'test.de'"))
        self.assertEqual(count, 1)

        result = root.domains.select(sql.where("domain.fqdn > 'u'"))
        fqdns = map(lambda domain: domain.fqdn, result)
        self.assertEqual(fqdns[0], "vorberg.name")
        
        # unlink
        two.domains.unlink(domains[1])
        self.assertEqual(len(two.domains), 1)

        two.domains.unlink_by_primary_key(sql.integer_literal(3))
        self.assertEqual(len(two.domains), 0)


class many2many_test_pgsql(many2many_test):
    """
    Incarnation of the many2many example for pgsql. As you can see I
    like to use PostgreSQL's advanced features (as compared to gadfly
    or even common MySQL usage), as for instance sequences and
    constraints. The sequences are implicitly created by using the
    SERIAL column type. In fact, serial is just a shorthand. Refer to
    the PostgreSQL documentation for detailed info.
    """
    
    def setUp(self):
        self.ds = datasource(os.getenv("ORMTEST_PGSQL_CONN"))

        self.ds.execute("""CREATE TABLE domain (
                             id SERIAL PRIMARY KEY,
                             fqdn TEXT UNIQUE
                           )""")

        self.ds.execute("""CREATE TABLE mail_admin (
                             id SERIAL PRIMARY KEY,
                             email TEXT UNIQUE,
                             name TEXT
                           )""")

        self.ds.execute("""CREATE TABLE mail_server (
                             id SERIAL PRIMARY KEY,
                             fqhn TEXT UNIQUE
                           )""")

        self.ds.execute("""CREATE TABLE domain_to_mail_admin (
                             domain_id INTEGER REFERENCES domain,
                             mail_admin_id INTEGER REFERENCES mail_admin,

                             UNIQUE(domain_id, mail_admin_id)
                           )""")

        self.ds.execute("""CREATE TABLE mail_admin_to_mail_server (
                             admin_email TEXT REFERENCES mail_admin(email),
                             server_hostname TEXT REFERENCES mail_server(fqhn)
                           )""")


class many2many_test_mysql(many2many_test):
    """
    """
    
    def setUp(self):
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS domain")
        self.ds.execute("""CREATE TABLE domain (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                      PRIMARY KEY(id),
                             fqdn VARCHAR(100) UNIQUE
                           )""")

        self.ds.execute("DROP TABLE IF EXISTS mail_admin")
        self.ds.execute("""CREATE TABLE mail_admin (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                      PRIMARY KEY(id),
                             email VARCHAR(100) UNIQUE,
                             name VARCHAR(100)
                           )""")

        self.ds.execute("DROP TABLE IF EXISTS mail_server")
        self.ds.execute("""CREATE TABLE mail_server (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                                      PRIMARY KEY(id),
                             fqhn VARCHAR(100) UNIQUE
                           )""")

        self.ds.execute("DROP TABLE IF EXISTS domain_to_mail_admin")
        self.ds.execute("""CREATE TABLE domain_to_mail_admin (
                             domain_id INTEGER REFERENCES domain,
                             mail_admin_id INTEGER REFERENCES mail_admin,

                             UNIQUE(domain_id, mail_admin_id)
                           )""")

        self.ds.execute("DROP TABLE IF EXISTS mail_admin_to_mail_Server")
        self.ds.execute("""CREATE TABLE mail_admin_to_mail_server (
                             admin_email VARCHAR(100)
                                                  REFERENCES mail_admin(email),
                             server_hostname VARCHAR(100)
                                                  REFERENCES mail_server(fqhn)
                           )""")



if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(many2many_test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(many2many_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(many2many_test_mysql))

    unittest.TextTestRunner(verbosity=1).run(suite)
