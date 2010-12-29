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
# $Log: multiple_column_foreign_key.py,v $
# Revision 1.4  2006/09/04 16:00:01  diedrich
# There is no test adapter anymore.
#
# Revision 1.3  2006/05/02 13:34:42  diedrich
# Added checks for MySQL (which turned up a few bugs in the whole of orm)
#
# Revision 1.2  2006/04/15 23:23:56  diedrich
# *** empty log message ***
#
# Revision 1.1  2006/02/25 18:06:54  diedrich
# Initial commit.
#
#

"""
This tests foreing keys with multiple columns.
"""

import os, unittest
from string import *

from orm2.debug import sqllog
# sqllog.verbose = True

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.relationships import *
from orm2 import sql

from orm2.datasource import datasource


# Model
class domain(dbobject):
    __primary_key__ = ( "domain", "tld", )
    domain = text()
    tld = text()

class email(dbobject):
    id = common_serial()
    local_part = text()
    remote_part_domain = text()
    remote_part_tld = text()
    
    domain = many2one(domain, child_key=None,
                      foreign_key=("remote_part_domain", "remote_part_tld", ))

domain.emails = one2many(email, child_key=("remote_part_domain",
                                           "remote_part_tld",))

class domain_and_email_test(unittest.TestCase):
    def setUp(self):
        self.ds = datasource("adapter=gadfly")

        self.ds.execute("""CREATE TABLE domain (
                             domain VARCHAR,
                             tld VARCHAR
                           )""")
        
        self.ds.execute("""CREATE TABLE email (
                             id INTEGER,
                             local_part VARCHAR,
                             remote_part_domain VARCHAR,
                             remote_part_tld VARCHAR
                           )""")

    data = ( ("tux4web.de", ("info", "support", "diedrich", "spam"),),
             ("apple.com", ("steve", "store", "webmaster",),),)

    def test(self):
        for fqdn, emails in self.data:
            dom, tld = split(fqdn, ".")
            new_domain = domain(domain=dom, tld=tld)
            self.ds.insert(new_domain)

            for addr in emails:
                new_domain.emails.append(
                    email(remote_part_domain=dom, remote_part_tld=tld,
                          local_part=addr))
                
        # Let's check...
        tux4web = self.ds.select_one(domain, sql.where("domain='tux4web'"))
        self.assertEqual(len(tux4web.emails), 4)

        apple = self.ds.select_by_primary_key(domain, ("apple", "com",))
        self.assertEqual(len(apple.emails), 3)

        result = apple.emails.select(sql.where("local_part = 'steve'"))
        steve = result.next()

        self.assertEqual(steve.local_part, "steve")
        self.assertEqual(steve.remote_part_domain, "apple")

        # The other way 'round
        emails = self.ds.select(email)

        # This will yield one select statement for each email.
        # This effect can be prevented by using SQL joins.
        # This is being worked on.
        for a in emails:
            self.assertEqual(a.remote_part_domain, a.domain.domain)


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
                             domain TEXT,
                             tld TEXT,

                             PRIMARY KEY (domain, tld)
                           )""")
        self.ds.execute("""CREATE TABLE email (
                             id SERIAL,
                             local_part VARCHAR,
                             remote_part_domain TEXT,
                             remote_part_tld TEXT,

                             PRIMARY KEY (id),
                             FOREIGN KEY (remote_part_domain, remote_part_tld)
                                REFERENCES domain (domain, tld)
                           )""")


class domain_and_email_test_mysql(domain_and_email_test):
    def setUp(self):
        # ORMTEST_MYSQL_CONN="adapter=mysql host=localhost dbname=test"
        self.ds = datasource(os.getenv("ORMTEST_MYSQL_CONN"))

        self.ds.execute("DROP TABLE IF EXISTS domain", modify=True)
        self.ds.execute("DROP TABLE IF EXISTS email", modify=True)
        
        self.ds.execute("""CREATE TABLE domain (
                             domain VARCHAR(255),
                             tld VARCHAR(10),

                             PRIMARY KEY (domain, tld)
                           )""")
        
        self.ds.execute("""CREATE TABLE email (
                             id INTEGER NOT NULL AUTO_INCREMENT,
                             local_part VARCHAR(100),
                             remote_part_domain VARCHAR(255),
                             remote_part_tld VARCHAR(10),

                             PRIMARY KEY (id),
                             FOREIGN KEY (remote_part_domain, remote_part_tld)
                                REFERENCES domain (domain, tld)
                           )""")



if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(domain_and_email_test))

    if os.environ.has_key("ORMTEST_PGSQL_CONN"):
        suite.addTest(unittest.makeSuite(domain_and_email_test_pgsql))

    if os.environ.has_key("ORMTEST_MYSQL_CONN"):
        suite.addTest(unittest.makeSuite(domain_and_email_test_mysql))

    unittest.TextTestRunner(verbosity=2).run(suite)
   
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:
