#!/usr/bin/python
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
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
# $Log: test_resource_identifyer.py,v $
# Revision 1.1  2006/08/23 12:39:43  t4w00-diedrich
# Initial commit.
#
#

"""
Unit test for the dsc.resource_identifyer and dsc.resource_set classes
"""

from string import *
import os, unittest

from psg.document.dsc import resource_identifyer, resource_set

class Test(unittest.TestCase):
    comment_arg = """font Times-Roman Helvetica StoneSerif\r
                     font Adobe-Garamond Palatino-Roman
                     file /usr/lib/PostScript/logo.ps
                     procset Adobe_Illustrator_abbrev 1.0 0
                     pattern hatch bubbles
                     form (corporate order form)
                     encoding JIS"""
    
    def test(self):
        c = replace(self.comment_arg, "\n", "\r")        
        s = resource_set.from_string(c)

        #for a in s:
        #    print a
        
        self.assert_(len(s) == 11)
        
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    unittest.TextTestRunner(verbosity=2).run(suite)





# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

