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
# $Log: __init__.py,v $
# Revision 1.6  2006/09/07 13:56:32  diedrich
# Added module_property class.
#
# Revision 1.5  2006/05/08 22:41:54  diedrich
# Added import_with_new_modules()
#
# Revision 1.4  2006/04/28 09:49:26  diedrich
# Docstring updates for epydoc
#
# Revision 1.3  2006/01/01 20:48:40  diedrich
# Added the stupid_dict class.
#
# Revision 1.2  2005/12/31 18:33:06  diedrich
# Updated year in copyright header ;)
#
# Revision 1.1  2005/11/21 19:50:23  diedrich
# Initial commit
#
#

"""
This module defines a number of miscellaneous helper functions and classes.
"""

import sys
from types import *
from string import *
import imp
python_import = __builtins__.__import__

_replacement_modules = {}

def _my_import(name, g, l, from_list):
    global _replacement_modules

    if _replacement_modules.has_key(name):
        return _replacement_modules[name]
    else:
        return python_import(name, g, l, from_list)

def import_with_new_modules(module_name, replacement_modules={}):
    """
    This is a nifty function that allows your modules to inherit from each
    other maintaining upward compatibility with regard as (for instance)
    orm2 based data models.

    Example:

    >>> import model2
    >>> controllers1 = import_with_new_modules('mytest.sub.controllers1',
                                               {'model1': model2})

    >>> email = controllers1.make_email()
    >>> print email.__module__
    model2

    The controllers1.py module was written for a datamodel stored in the
    model1.py module in the same package. So it imports it. Now, the function
    calls above will import controllers1 with model2 as its datamodel. Of
    course the new module must be a super set of the old for this to work.
    (In this example the email class has been extended by an attribute.)

    @param module_name: The name of the module to import (including
       package name(s))
    @param replacement_modules: A dictionary mapping module names (<b>as
       they are imported by the module references by module_name</b>) and the
       module object it is supposed to be replaces with.

    """
    global _replacement_modules
    
    imp.acquire_lock()
    parts = split(module_name, ".")

    path = None
    for package in parts[:-1]:
        file, filename, description = imp.find_module(package, path)
        module = imp.load_module(package, file, filename, description)
        path = module.__path__
    
    file, filename, description = imp.find_module(parts[-1], module.__path__)
    module = imp.load_module(module_name, file, filename, description)
    
    globs = module.__dict__.copy()
    _replacement_modules = replacement_modules
    
    filename = module.__file__
    if filename.endswith("pyc"): filename = filename[:-1]

    __builtin__.__import__ = _my_import
    execfile(filename, globs)
    __builtin__.__import__ = python_import
    imp.release_lock()
    
    module = imp.new_module("imported with new modules: %s %s" % \
                            (module.__name__, repr(replacement_modules),))
    module.__dict__.update(globs)
    return module









class stupid_dict:
    """
    This class implements the mapping (dict) interface. It uses a
    simple list to store its data and sequential search to access
    it. It does not depend on __hash__() to manage contained
    objects. (See Python Reference Manual Chapter 3.3)

    The actual data is stored in self.data as a list of tuples like
    (key, value).

    See the docstring of orm2.sql._part for details on why this is here.
    """
    def __init__(self, initdata=[]):
        if type(initdata) in (ListType, TupleType,):
            self.data = []
            for tpl in initdata:
                if type(tpl) not in (ListType, TupleType) or len(tpl) != 2:
                    raise ValueError("Cannot inittiate stupid_dict from "+\
                                     "that data")
                else:
                    self.data.append(tpl)
        elif type(initdata) == DictType:
            self.data = initdata.items()
        else:
            raise ValueError("A stupid_dict must be initialized either by "+\
                             "a list of pairs or a regular dictionary.")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, which):
        for key, value in self.data:
            if key == which:
                return value

        if hasattr(self, "default"):
            return self.default
        else:
            raise KeyError(what)

    def __setitem__(self, which, what):
        if self.has_key(which):
            self.__delitem__(which)
            
        self.data.append( (which, what,) )

    def __delitem__(self, which):
        if self.has_key(which):
            idx = self.keys().index(which)
            del self.data[idx]
        else:
            raise KeyError(which)


    def __iter__(self):
        for key, value in self.data: yield key


    def __contains__(self, which):
        return which in self.keys()

    def __cmp__(self, other):
        raise NotImplementedError("I have no idea on how to do this...")
        
    def __eq__(self, other):
        self.data.sort()
        other.data.sort()
        
        if self.data == other.data:
            return True
        else:
            return False

    def __repr__(self):
        return "stupid_dict(%s)" % repr(self.data)

    def clear(self):
        self.data = []

    def copy(self):
        return stupid_dict(self.data[:])

    def get(self, which, default=None):
        if self.has_key(which):
            return self[which]
        else:
            return default

    def has_key(self, which):
        if which in self.keys():
            return True
        else:
            return False

    def items(self):
        return self.data[:]

    def iteritems(self):
        for tpl in self.data: yield tpl

    iterkeys = __iter__
    
    def itervalues(self):
        for key, value in self.data: yield value

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def pop(self):
        raise NotImplementedError("This doesn't make sense in a stupid_dict,"+\
                                  " or does it? No, seriously...")

    popitem = pop

    def setdefault(self, default):
        self.default = default

    def update(self, other):
        """
        Other must implement the mapping (i.e. dict) interface.
        """
        for key, value in other.items():
            self[key] = value

    
class module_property(property):
    """
    Property class the will return the module object of the module the
    owning class was loaded from.
    """
    def __get__(self, dbobj, owner=None):
        return sys.modules[dbobj.__class__.__module__]
    
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

