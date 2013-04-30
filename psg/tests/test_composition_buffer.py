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
# $Log: test_composition_buffer.py,v $
# Revision 1.2  2006/08/23 12:41:35  t4w00-diedrich
# Updated the tests.
#
# Revision 1.1  2006/08/18 17:39:49  t4w00-diedrich
# Initial commit
#
#
#

"""
Unit test for the composition buffer class. 
"""

import os, unittest
from cStringIO import StringIO as cStringIO

from psg.util import composition_buffer
from psg.exceptions import *

class composition_buffer_test(unittest.TestCase):
    def nested_buffer(self):
        b = composition_buffer()
        
        hello = composition_buffer( ("Hallo",) )
        b.append( hello )
        b.hello = hello

        world = composition_buffer( ("Welt",) )
        b.append(world)
        b.world = world

        return b
                 
    
    def test_init(self):
        def r(): buffer = composition_buffer([])

        #self.assertRaises(TypeError, r)

    def test_write(self):
        def r():
            b = composition_buffer()
            b.write(x())

        self.assertRaises(TypeError, r)

        def s():
            b = composition_buffer()
            b.close()
            b.write("Hallo")

        self.assertRaises(IllegalFunctionCall, s)
        
    
    def test_as_string(self):
        b = composition_buffer()
        b.write("Hallo ")
        b.write("Welt!")

        self.assertEqual("Hallo Welt!", b.as_string())

    def test_write_to(self):
        b = self.nested_buffer()
        fp = cStringIO()

        b.write_to(fp, up_to = b.world, close=True)
        self.assertEqual("Hallo", fp.getvalue())

        def r(buff):
            buff.write(" ")

        # The first buffer may not be written to any more.
        self.assertRaises(IllegalFunctionCall, r, b.hello)

    

class x: pass        

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(composition_buffer_test))
    unittest.TextTestRunner(verbosity=2).run(suite)





# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

