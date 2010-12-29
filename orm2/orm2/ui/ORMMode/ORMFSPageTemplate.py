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
# $Log: ORMFSPageTemplate.py,v $
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
#

# Changelog (orm)
# ---------------
#
# $Log: ORMFSPageTemplate.py,v $
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
# Revision 1.9  2004/10/02 11:37:49  t4w00-diedrich
# The user variable is not only available within the pt but also in the
# parameters dict.
#
# Revision 1.8  2004/08/30 11:06:47  t4w00-diedrich
# - added Security tab
# - added "Call ORM mode function" Zope permission
#
# Revision 1.7  2004/08/28 13:54:53  t4w00-diedrich
# Added processing of path variables.
#
# Revision 1.6  2004/08/18 10:21:43  t4w00-diedrich
# Provide a user variable within the PageTemplate like CMFFSPageTemplate
# does. This is required for Plone to work with us
#
# Revision 1.5  2004/08/03 16:33:38  t4w00-diedrich
# Changed to Implicit Acquisition
#
# Revision 1.4  2004/08/03 10:52:26  t4w00-diedrich
# Added db_charset parameter.
#
# Revision 1.3  2004/08/03 09:23:26  t4w00-diedrich
# Added caching support
#
# Revision 1.2  2004/08/03 07:39:52  t4w00-diedrich
# Actually use the PageTemplate interface.
#
# Revision 1.1  2004/08/02 23:04:43  t4w00-diedrich
# Initial commit
#
#
#

# Python
import sys, os
from string import split, join
from types import StringType
import re

# Zope
from Globals import DevelopmentMode
from Products.PageTemplates.PageTemplate import PageTemplate
from App.config import getConfiguration
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.Expressions import SecureModuleImporter
from OFS.SimpleItem import Item
from AccessControl import ClassSecurityInfo
from OFS.Cache import Cacheable
from Acquisition import Implicit
from AccessControl import getSecurityManager

# ORMMode
from ORMMode import ORMMode, ORMModeException

class InvalidPathOrigin(ORMModeException): pass
class InvalidFilePath(ORMModeException): pass

def manage_addORMFSPageTemplate(self, id, module_name, mode_function_name,
                                db_connection_name, db_charset,
                                file_path, path_origin,
                                session_on=False,
                                path_variables_on=False, path_variables="",
                                REQUEST=None):
    """
    Add an ORMFSPageTemplate Object to the current Zope instance
    """
    id = str(id)
    
    module = str(module_name)
    mode_function = str(mode_function_name)
    db_connection = str(db_connection_name)
    db_charset = str(db_charset)

    file_path = str(file_path)
    path_origin = str(path_origin)

    if str(session_on) == "on":
        session_on = True
    else:
        session_on = False

    if str(path_variables_on == "on"):
        path_variables_on = True
    else:
        path_variables_on = False
        

    obj = ORMFSPageTemplate(id, module, mode_function,
                            db_connection, db_charset, session_on,
                            path_variables_on, path_variables,
                            file_path, path_origin)
    self._setObject(id, obj)

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

manage_addORMFSPageTemplateForm = PageTemplateFile("www/ORMFSPageTemplate.pt",
                                                   globals())

class ORMFSPageTemplate(Implicit, ORMMode, PageTemplate):
    """
    This object type combines ORMMode and Zope's PageTemplates. The
    mode functions's return falue is made available within the page
    template as rt ('return value') and can be used in any tal
    expression.    
    """
    security=ClassSecurityInfo()

    meta_type = "ORM Filesystem Page Template"

    manage_main = PageTemplateFile("www/ORMFSPageTemplate.pt", globals())

    manage_options = (
    (
        {"label": "Edit", "action": "manage_main"},
        {"label": "Security", "action": "manage_access"}
    ) + Item.manage_options + Cacheable.manage_options)

    # The same permissions like External Methods
    __ac_permissions__ = (
        ('View management screens', ('manage_main',)),
        ('Change Page Templates', ('manage_edit',)),
        ('View', ('__call__','')),
        )

    # Declare security for unprotected PageTemplate methods.
    security.declarePrivate('pt_edit', 'write')
    
    def __init__(self, id, module_name, mode_function_name,
                 db_connection_name, db_charset, session_on,
                 path_variables_on, path_variables,
                 file_path, path_origin, REQUEST=None):
        self.id = id
        self.manage_edit(module_name, mode_function_name,
                         db_connection_name, db_charset,
                         file_path, path_origin, session_on,
                         REQUEST)

    def manage_edit(self, module_name, mode_function_name,
                    db_connection_name, db_charset,
                    file_path, path_origin, session_on=False,
                    path_variables_on=False, path_variables="",
                    REQUEST=None):
        """
        Edit the current object.
        """
        ORMMode.manage_edit(self, module_name, mode_function_name,
                            db_connection_name, db_charset, session_on,
                            path_variables_on, path_variables,
                            None)

        self._file_path = file_path

        if path_origin not in ("root", "module", "instance"):
            raise InvalidPathOrigin(path_origin)
        
        self._path_origin = path_origin

        # read the source file to see if it's there and pass the
        # result to PageTemplate (write method)
        self.write(self.source())
        
        if REQUEST is not None:
            message="ORMFSPageTemplate updated."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)
        
    def file_path(self):
        "Accessor."
        return self._file_path

    def path_origin(self):
        "Accessor."
        return self._path_origin

    def base_dir(self):
        """
        Return the beginning of the source file path determined by
        the path_origin (including a trailing path seperator).

        If path_origin is 'root' it returns '', because the file_path
        is supposed to be absolute.

        If the file_path() is absolute already it will return '',
        too.
        """
        if os.path.isabs(self.file_path()):
            return ""
        elif self.path_origin() == "root":
            return os.path.sep
        elif self.path_origin() == "module":
            tpl = os.path.split(self.module().__file__)
            module_path = tpl[0]

            return module_path + os.path.sep
        elif self.path_origin() == "instance":
            cfg = getConfiguration()
            if cfg.instancehome[-1] == os.path.sep:
                return cfg.instancehome
            else:
                return cfg.instancehome + os.path.sep
            

    def source(self):
        """
        Return the contents of the file pointed to by file_path and
        path_origin
        """
        path = self.base_dir() + self.file_path()
        f = open(path)        
        return f.read()

    def __call__(self):
        if DevelopmentMode:
            self.write(self.source())
        
        result = self.ZCacheable_get(default=None)
        if result is None:
            result = self.pt_render()
            self.ZCacheable_set(data=result)

        return result
    
    def pt_getContext(self):
        security=getSecurityManager()
        
        # this is from ZopePageTemplate, mostly.
        root = self.getPhysicalRoot()
        user = security.getUser()
        c = {'template': self,             
             'here': self,
             'context': self,
             'container': self.aq_parent,
             'nothing': None,
             'options': {},
             'root': root,
             'request': getattr(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             'parent': self.aq_parent,
             'inner': self.aq_inner,
             'container': self.aq_parent,
             'user': user, # CMFCore.FSPageTemplate defines this.
                           # That's why it's needed for Plone to
                           # work.
             'rv': self.om_exec(user=user) # also pass the user object to the 
             }                             # mode functin. Can't hurt :-) 
        return c
    
