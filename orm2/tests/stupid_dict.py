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
# $Log: stupid_dict.py,v $
# Revision 1.1  2006/01/01 20:37:48  diedrich
# Initial comit (half way into many2many)
#
# Revision 1.1  2005/12/18 22:33:43  diedrich
# Initial commit
#
#

"""
Test all the methods in the stupid dict class. Uff!
"""

import os, unittest
from types import *

from orm2.util import stupid_dict

class test_stupid_dict(unittest.TestCase):
    sampleA = { "A": 1, "B": 2, "C": 3 }
    sampleB = ( (1, "A",), (2, "B",), (3, "C",), )
    sampleC = { "B": "b", "D": 4 }
    samples = ( sampleA, sampleB, sampleC, )
    
    def test__init__(self):
        self.assertRaises(ValueError, stupid_dict, ( (1, 2,), 1, 2, ))
        self.assertRaises(ValueError, stupid_dict, "kacke")

        d = stupid_dict({"a": 1, "b": 2})

    def test__len__(self):
        for a in self.samples:
            d = stupid_dict(a)
            self.assertEqual(len(d), len(a))
            
    def test__getitem__(self):
        for sample in self.samples:
            a = stupid_dict(sample)

            if type(sample) == DictType:
                items = sample.items()
            else:
                items = sample

            for key, value in items:
                self.assertEqual(a[key], value)
        
    def test__setitem__(self):
        d = stupid_dict(self.sampleA)
        d["D"] = 4

        self.assert_( ("D", 4,) in d.data )
            
    def testkeys(self):
        d = stupid_dict(self.sampleB)
        self.assert_(d.keys() == [ 1, 2, 3, ])

    def test__delitem__(self):
        d = stupid_dict(self.sampleC)
        
        del d["B"]

        self.assertEqual(d.data, [("D", 4,)])

        self.assertRaises(KeyError, d.__delitem__, "X")
        
    def test__iter__(self):
        d = stupid_dict(self.sampleC)

        l = []
        for key in d:
            l.append(key)

        self.assertEqual(l, ["B", "D"])

    def test__contains__(self):
        d = stupid_dict(self.sampleC)
        
        self.assert_("B" in d)
        self.assert_(not "X" in d)
        
    def test__eq__(self):
        d1 = stupid_dict(self.sampleC)
        d2 = stupid_dict((("B", "b",), ("D", 4,),))

        self.assertEqual(d1, d2)
        
    def test__repr__(self):
        d = stupid_dict(self.sampleB)
        self.assertEqual(repr(d), "stupid_dict(%s)" % repr(list(self.sampleB)))
        
    def testclear(self):
        d = stupid_dict(self.sampleB)
        d.clear()
        self.assertEqual(len(d), 0)
        
    def testcopy(self):
        d = stupid_dict(self.sampleB)
        e = d.copy()

        self.assert_(id(d) != id(e) and d == e)
        
    def testget(self):
        d = stupid_dict(self.sampleB)

        self.assertEqual(d.get(1), "A")
        self.assertEqual(d.get(0, "X"), "X")
        self.assertEqual(d.get(0), None)
        
    def testhas_key(self):
        d = stupid_dict(self.sampleB)

        self.assert_(d.has_key(1))
        self.assert_(not d.has_key(0))
        
    def testitems(self):
        d = stupid_dict(self.sampleB)
        self.assertEqual(d.items(), list(self.sampleB))
        
    def testvalues(self):
        d = stupid_dict(self.sampleB)
        self.assertEqual(d.values(), [ "A", "B", "C", ])

    def testsetdefault(self):
        d = stupid_dict(self.sampleB)
        d.setdefault("X")

        self.assert_(d[0] == "X")
        self.assert_(d[1] == "A")
        
    def testupdate(self):
        a = stupid_dict(self.sampleA)
        c = stupid_dict(self.sampleC)

        a.update(c)

        self.assert_( a["A"] == 1)
        self.assert_( a["B"] == "b")
    
if __name__ == '__main__':
    unittest.main()
        
    
        
