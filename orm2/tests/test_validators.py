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
# $Log: test_validators.py,v $
# Revision 1.1  2006/05/13 14:56:56  diedrich
# Initial commit
#
#

"""
Test various aspects of the validator mechanism
"""

import os, unittest

from orm2.debug import sqllog
sqllog.verbose = True
sqllog.buffer_size = 10 # keep the last 10 sql commands sent to the backend

from orm2.dbobject import dbobject
from orm2.datatypes import *
from orm2.datasource import datasource
from orm2.validators import *
from orm2.util.datatypes import *

class verbose_test(dbobject):
    __primary_key__ = None
    
    no_null = integer(validators=(not_null_validator(),))
    teenager = integer(validators=(range_validator(13, 19, include_bounds=True)),)
    twen = integer(validators=(range_validator(19, 30),))
    normal_domain = varchar(256, validators=(re_validator(domain_name_re),))
    punicode_domain = PDomain()
    punicode_email = PEMail()

class validator_test(unittest.TestCase):

    def setUp(self):
        self.dbobj = verbose_test()
    
    def test_not_null(self):
        self.dbobj.no_null = 42

        def fail():
            self.dbobj.no_null = None

        self.assertRaises(NotNullError, fail)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(validator_test))
        

    unittest.TextTestRunner(verbosity=1).run(suite)

