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

# Changelog (orm2)
# ---------------
# $Log: __init__.py,v $
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
#

# Changelog (orm)
# ---------------
#
# $Log: __init__.py,v $
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
# Revision 1.2  2004/08/02 23:05:35  t4w00-diedrich
# Added OEMFSPageTemplate.
#
# Revision 1.1  2004/08/01 15:44:02  t4w00-diedrich
# Initial commit.
#
#
#

"""
Python product that fullfills a simmilar function as ExternalMethod
except that will call any callable, mostly classes that inherit from
the mode class below, instead of just Python functions. (Remember,
calling a class will return an instance). The callable MUST have a
**kw parameter for arbitrary key word arguments for this to
work. Anyway, think of modes as External Methods which have
overloadable parts.
"""

import ORMMode
import ORMFSPageTemplate

def initialize(context):
    context.registerClass(
        ORMMode.ORMMode,
        permission='Add ORM Mode Object',
        constructors=(ORMMode.manage_addORMModeForm,
                      ORMMode.manage_addORMMode),
        #icon='www/PageXML.gif',
        )

    
    context.registerBaseClass(ORMMode.ORMMode)

    context.registerClass(
        ORMFSPageTemplate.ORMFSPageTemplate,
        permission='Add ORM Mode Object',
        constructors=(ORMFSPageTemplate.manage_addORMFSPageTemplateForm,
                      ORMFSPageTemplate.manage_addORMFSPageTemplate),
        #icon='www/PageXML.gif',
        )

    
    context.registerBaseClass(ORMFSPageTemplate.ORMFSPageTemplate)




class mode(object):
    """
    Baseclass for orm modes. A class that inherits from mode behaves just
    like a function whoes parts may be overwritten. When instantiated a mode
    class will not return an instance of itselt, but the result of an
    instance's __call__ method. Example

    >>> from orm.ui.modes import mode
    >>> class test(mode):
    ...     def __call__(self, para):
    ...             return para * 2
    ... 
    >>> x = test(5)
    >>> x
    10
    """
    def __new__(cls, *args, **kw):
        instance = object.__new__(cls)
        return instance(*args, **kw)

