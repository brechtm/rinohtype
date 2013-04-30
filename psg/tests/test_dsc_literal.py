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
# $Log: test_dsc_literal.py,v $
# Revision 1.1  2006/08/19 15:43:34  t4w00-diedrich
# Initial commit
#

#
#
#

"""
Unit test for the dsc.parse_literal() function
"""

import os, unittest
from cStringIO import StringIO

from psg.document.dsc import parse_literals

class composition_buffer_test(unittest.TestCase):
    def test(self):
        tpl = parse_literals("0 0 596 842", "iiii")
        self.assertEqual(tpl, (0, 0, 596, 842,))
        
        tpl = parse_literals("procset Adobe_AGM_Utils 1.0 0", "ssff")
        self.assertEqual(tpl, ('procset', 'Adobe_AGM_Utils', 1.0, 0.0,))
        
        tpl = parse_literals("Copyright (C) 1997-2003 Adobe Systems, Inc.  All Rights Reserved.", "l")
        self.assertEqual(tpl, ("Copyright (C) 1997-2003 Adobe Systems, Inc.  All Rights Reserved.", ))
            
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(composition_buffer_test))
    unittest.TextTestRunner(verbosity=2).run(suite)





# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

