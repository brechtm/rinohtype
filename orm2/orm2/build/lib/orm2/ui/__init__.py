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

#
# $Log: __init__.py,v $
# Revision 1.8  2006/09/19 14:26:25  diedrich
# View_spec.import_() uses the sys.modules cache to speed things
# up. Also in debugging mode, it reload() to make sure changes matter.
#
# Revision 1.7  2006/09/07 13:56:16  diedrich
# Added widget_spec mechanism (again).
#
# Revision 1.6  2006/09/04 15:56:26  diedrich
# The view class now has a method called ds() as opposed to an
# attribute. (This reverts to a previous state due to practical
# experience).
#
# Revision 1.5  2006/07/08 17:10:53  diedrich
# Changed view.ds() to view.ds like in procedure
#
# Revision 1.4  2006/07/04 22:48:41  diedrich
# Added belongs_to() method to widget class.
#
# Revision 1.3  2006/06/10 18:06:12  diedrich
# Rewrote widget handling
#
# Revision 1.2  2006/05/15 21:49:10  diedrich
# Working on ui basics
#
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
#

"""
Someday there will be user interface 'glue' in this module. Now there
is just a lot of undocumented code that makes no sense.
"""

import sys, thread, imp
from string import *
from orm2 import debug

######################################################################
## Widgets
######################################################################

_widget_index = 1

class widget:    
    def __init__(self, **kw):
        global _widget_index

        self.params = kw
        
        lock = thread.allocate_lock()
        lock.acquire()
        self.__index__ = _widget_index
        _widget_index += 1
        lock.release()
        
    def __init_dbproperty__(self, dbproperty):
        self.dbproperty = dbproperty

    def __cmp__(self, other):
        """
        This makes sort() on sequences of widget objects use the _widget_index
        for sorting
        """
        return cmp(self.__index__, other.__index__)

    def belongs_to(self, module_name):
        raise NotImplementedError()

    def __call__(self, dbobj, **kw):
        params = self.params.copy()
        params.update(kw)

        return self.actual_widget(dbobj, self.dbproperty, **params)

    class actual_widget:
        def __init__(self, dbobj, dbproperty, **kw):
            self.dbobj = dbobj
            self.dbproperty = dbproperty
            
            for name, value in kw.items():
                setattr(self, name, value)

                

######################################################################
## Views
######################################################################

class view:
    def __init__(self, dbobj=None, result=None):
        self.dbobj = dbobj
        if dbobj is not None: self.dbclass = dbobj.__class__
            
        self.result = result
        if result is not None: self.dbclass = result.dbclass

        if (dbobj is None and result is None) or \
           (dbobj is not None and result is not None):
            raise ValueError("A view must be initialized either with " + \
                             "dbobj XOR result set to an appropriate value")

        if self.dbobj is not None:
            self._ds = dbobj.__ds__()
        else:
            self._ds = result.ds

    def ds(self):
        if self._ds is None:
            if self.dbobj is not None:
                self._ds = self.dbobj.__ds__()
            else:
                self._ds = self.result.ds

                
            if self._ds is None:
                raise ValueError("Plase make sure any dbobj you use with a  "+\
                                 "view knows a datasource (use the __ds "+ \
                                 "param to its constructor!)")
        else:
            return self._ds


class view_spec:
    """
    The view spec class provides a mechanism to lazily load views at runtime.
    This avoids infinite loops in complex module hierarchies that have
    seperate modules for dbclasses and views. Defining you dbclass like this::

       class font(dbobject):
           id = serial()
           ps_name = text()
           user_name = Unicode()

           preview = view_spec('myproject.views.font')

    will cause the myproject.views.font module to be loaded. It must contain
    a class names prevew which inherits from orm2.ui.view. This class will be
    instantiated and put into the font dbobject on initialization.
    """
    def __init__(self, module_name):
        self.module_name = module_name

    def import_(self, class_name):
        if sys.modules.has_key(self.module_name):
            module = sys.modules[self.module_name]
            if debug.debug.verbose:
                reload(module)
        else:
            complete_module_name = self.module_name
            module_path = split(complete_module_name, ".")
            module_name = module_path[-1]
            module_path = join(module_path, ".")
        
            module = __import__(module_path,
                                globals(), locals(),
                                module_name)

            sys.modules[self.module_name] = module

        return getattr(module, class_name)

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

