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
# $Log: ORMMode.py,v $
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
#

# Changelog (orm)
# ---------------
#
# Revision 1.26  2005/05/08 21:03:42  t4w00-diedrich
# Reverted to old bahaviour in __before_publishing_traverse__
#
# Revision 1.25  2005/05/08 15:59:09  t4w00-diedrich
# __before_publishing_traverse__ uses __dict__.has_key instead of hasattr()
# to check whether one of its own methods is called
#
# Revision 1.24  2005/02/21 13:10:09  t4w00-diedrich
# HTTP_USER_AGENT and other client environment variables are passed to
# the mode now
#
# Revision 1.23  2005/01/11 18:12:07  t4w00-diedrich
# Added HTML PUT support (which just calls the __call__() method. The
# mode has to differntiate between GET and PUT calls by checking
# request["REQUEST_METHOD"]
#
# Revision 1.22  2004/12/12 18:25:55  t4w00-diedrich
# Uncought UnicodeException in __before_publishing_traverse__() has
# caused some trouble
#
# Revision 1.21  2004/11/16 16:45:33  t4w00-diedrich
# Updated to use new zpsycopg_db_conn class instead of the old mechanism
#
# Revision 1.20  2004/10/02 16:05:43  t4w00-diedrich
# New, much improved handling of module modificaton time
#
# Revision 1.19  2004/09/05 00:37:59  t4w00-diedrich
# Rollback the ds *after* it has been used by the mode function. If the
# mode function has not commited its changes they will be lost.
#
# Revision 1.18  2004/08/30 11:06:47  t4w00-diedrich
# - added Security tab
# - added "Call ORM mode function" Zope permission
#
# Revision 1.17  2004/08/28 20:23:01  t4w00-diedrich
# Eventually renamed ds() _ds() to avoid naming conflicts.
#
# Revision 1.16  2004/08/28 13:54:53  t4w00-diedrich
# Added processing of path variables.
#
# Revision 1.15  2004/08/27 01:46:45  t4w00-diedrich
# Enable orm logging if in DevelopmentMode
#
# Revision 1.14  2004/08/20 14:03:49  t4w00-diedrich
# A request is assumed to be encoded in Python's defaultencoding instead
# iso-8859-1
#
# Revision 1.13  2004/08/18 12:25:21  t4w00-diedrich
# - Let the mode parameter overwrite the mode_function_name
# - Fixed mode_function()
#
# Revision 1.12  2004/08/18 10:22:18  t4w00-diedrich
# Changed error message
#
# Revision 1.11  2004/08/03 16:34:51  t4w00-diedrich
# - __call__() now accepts arbitrary arguments and parameters and passes
#   them to the mode function as one might expect. This lets one use
#   mode functions just like External Methods
# - context is passed to the mode function
#
# Revision 1.10  2004/08/03 12:07:19  t4w00-diedrich
# Also cache the Content-Type header.
#
# Revision 1.9  2004/08/03 11:52:25  t4w00-diedrich
# - add header to formdata
# - call __reload__() function even if the modes module has not been
#   modified
#
# Revision 1.8  2004/08/03 10:53:22  t4w00-diedrich
# - Added db_charset parameter
# - Get DPI database connection from Zope database connection object
#   and wrap it in an ORM adapter (currently pgsql only)
#
# Revision 1.7  2004/08/03 09:23:26  t4w00-diedrich
# Added caching support
#
# Revision 1.6  2004/08/03 09:11:33  t4w00-diedrich
# Implemented reloading mechanism
#
# Revision 1.5  2004/08/03 07:39:12  t4w00-diedrich
# Removed index_html() and renamed __call__() to om_exec() which is
# called by a new __call__() function.
#
# Revision 1.4  2004/08/02 23:05:22  t4w00-diedrich
# Both add and edit use the same form. Added App.Manage.Navigation to the
# parent classes to provide ZMI  management form elements.
#
# Revision 1.3  2004/08/01 23:13:39  t4w00-diedrich
# - optimzed session handling
# - optimized performance
# - wrote unicode conversion hack
#
# Revision 1.2  2004/08/01 18:31:55  t4w00-diedrich
# Finished writing the mode function's import and call functionality
#
# Revision 1.1  2004/08/01 15:44:02  t4w00-diedrich
# Initial commit.
#
#
#


# Python
import sys, os
from string import split, join
from types import StringType
import re

# Zope
from Acquisition import Implicit, Explicit, Acquired
from Persistence import Persistent
from AccessControl.Role import RoleManager
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import Item
from OFS import History
from Globals import MessageDialog, DevelopmentMode
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from App.Management import Navigation
from OFS.Cache import Cacheable

# orm
import orm
from orm.adapters.pgsql.datasource import zpsycopg_db_conn
import orm.debug

if DevelopmentMode:
    orm.debug.debug.verbose = True
    orm.debug.sqllog.verbose = True

class ORMModeException(Exception): pass
class NoSuchModule(ORMModeException): pass
class NoSuchFunction(ORMModeException): pass

class _header:
    """
    This is a port of the cgiutils header class to the Zope adapter.
    You might not want to use it from within Zope, only if you'd like
    to use you modes module with both Zope and cgiutils.
    """
    def __init__(self, response):
        self.response = response
    
    def set(self, field, value):
        self.response.setHeader(field, value)
        
    def append(self, field, value):
        self.response.setHeader(field, value)
        

    def redirect(self, url, **parameters):
        extra = []
        for param, value in parameters.items():
            value = url_quote(value)
            extra.append("%s=%s" % (param, value,) )

        extra = join(extra, "&")
        if extra != "": extra = "?" + extra

        content = "0; url=%s%s" % (url, extra, )

        self.set("refresh", content)

# see __call__ 
unwanted_request_keys = {
    'AUTHENTICATION_PATH' : 0, 'BASE1' : 0, 'BASE2' : 0, 'BASE3' : 0,
    'BASE4' : 0, 'GATEWAY_INTERFACE' : 0, 
    'HTTP_PRAGMA' : 0, 'PARENTS' : 0,
    'PATH_INFO' : 0, 'PATH_TRANSLATED' : 0, 'PUBLISHED' : 0,
    'RESPONSE' : 0, 'SCRIPT_NAME' : 0,
    'SERVER_NAME' : 0, 'SERVER_PORT' : 0, 'SERVER_PROTOCOL' : 0,
    'SERVER_SOFTWARE' : 0, 'SERVER_URL' : 0, 'SESSION' : 0,
    'TraversalRequestNameStack' : 0, 'URL' : 0, 'URL1' : 0, 'URL2' : 0,
    'URL3':0 }

charset_re=re.compile(r'text/[0-9a-z]+\s*;\s*charset=([-_0-9a-z]+' +
                      r')(?:(?:\s*;)|\Z)', re.IGNORECASE)

def manage_addORMMode(self, id, module_name, mode_function_name,
                      db_connection_name, db_charset,
                      session_on=False,
                      path_variables_on=False, path_variables="",
                      REQUEST=None):
    """
    Add an ORMMode Object to the current Zope instance
    """
    id = str(id)
    module = str(module_name)
    mode_function = str(mode_function_name)
    db_connection = str(db_connection_name)
    db_charset = str(db_charset)

    if str(session_on) == "on":
        session_on = True
    else:
        session_on = False

    if str(path_variables_on == "on"):
        path_variables_on = True
    else:
        path_variables_on = False
        
    obj = ORMMode(id, module, mode_function, db_connection, db_charset,
                  session_on, path_variables_on, path_variables)
    self._setObject(id, obj)

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

manage_addORMModeForm = PageTemplateFile("www/ORMMode.pt", globals())

class ORMMode(Explicit, Item, Persistent, RoleManager, Navigation, Cacheable):
    """
    This object type allows you to call ORM 'mode' functions from within
    your Zope application.
    """

    meta_type = "ORM Mode"
    manage_main = PageTemplateFile("www/ORMMode.pt", globals())

    manage_options = (
    (
        {"label": "Edit", "action": "manage_main"},
        {"label": "Test", "action": "test"},
        {"label": "Security", "action": "manage_access"}
    ) + Item.manage_options + Cacheable.manage_options )

    # The same permissions like External Methods
    __ac_permissions__ = (
        ('View management screens', ('manage_main',)),
        ('Change External Methods', ('manage_edit',)),
        ('Call ORM mode function', ('__call__','index_html')),
        )

    ZopeTime=Acquired
    HelpSys=Acquired    

    security = ClassSecurityInfo()

    def __init__(self, id, module_name, mode_function_name,
                 db_connection_name, db_charset, session_on,
                 path_variables_on, path_variables,
                 REQUEST=None):
        self.id = id
        self.manage_edit(module_name, mode_function_name,
                         db_connection_name, db_charset, session_on,
                         path_variables_on, path_variables,
                         REQUEST)
        
    def manage_edit(self, module_name, mode_function_name,
                    db_connection_name, db_charset, session_on=False,
                    path_variables_on=False, path_variables="",
                    REQUEST=None):
        """
        Modify the ORMMode object.
        """

        if getattr(self, "_module_name",
                   None) != module_name:
            self._module_name = module_name
            self._v_module = None
            self.module()

        if getattr(self, "_mode_function_name",
                   None) != mode_function_name:
            self._mode_function_name = mode_function_name
            self._v_mode_functions = {}
            self.mode_function()

        self._db_connection_name = db_connection_name
        self._db_charset = db_charset

        self._session_on = session_on

        self._path_variables_on = path_variables_on
        self._path_variables = split(path_variables, "/")

        self.ZCacheable_invalidate()
        
        if REQUEST is not None:
            message="ORM Mode updated."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)
    
    
    def __call__(self, *args, **kw):
        """
        Call the mode function and do cache management.
        """
        result = self.ZCacheable_get(default=None)

        if result is None:            
            data = self.om_exec(*args, **kw)
            mime_type = self.REQUEST.RESPONSE.headers.get(
                                                "content-type", "text/plain")
            self.ZCacheable_set(data=(data, mime_type))
        else:
            data, mime_type = result
            self.REQUEST.RESPONSE.setHeader("Content-Type", mime_type)
            
        return data
        

    def om_exec(self, *args, **kw):
        formdata = kw

        # figure out which charset was used to post the formdata.
        # This assumes, that the charset of the last REQUEST is the
        # same as that of the RESPONSE.
        # The data is actually sent url encoded and Zope converts it
        # to a string with a specific charset somewhere. I was unable
        # to figure out where and this is the best thing I came up
        # with... :-(

        # from ZPublisher/HTTPResponse.py

        encoding = sys.getdefaultencoding() # reasonable default
        
        # Try to figure out which encoding the request uses
        if self.REQUEST.RESPONSE.headers.has_key('content-type'):
            match = charset_re.match(
                self.REQUEST.RESPONSE.headers['content-type'])
            if match:
                encoding = match.group(1)
                
        # REQUEST contains tons of stuff that has not been passed by the
        # browser but which needs to be calculated for each request.
        # This is sorted out here. 
        for key in self.REQUEST.keys():
            if unwanted_request_keys.has_key(key):
                continue
            else:
                value = self.REQUEST[key]

                # convert to Unicode using sys.defaultencoding().
                # This must be set properly
                if type(value) == StringType:
                    try:
                        value = unicode(value, encoding)
                    except UnicodeDecodeError:
                        pass
                    
                formdata[key] = value


        ds = self._ds()

        # put together the stuff needed by the mode functions    
        formdata["ds"] = ds
        formdata["form"] = formdata
        formdata["base_url"] = self.absolute_url()
        formdata["request"] = self.REQUEST
        formdata["response"] = self.REQUEST.RESPONSE
        formdata["REQUEST"] = self.REQUEST
        formdata["RESPONSE"] = self.REQUEST.RESPONSE
        formdata["context"] = self.aq_parent
        formdata["header"] = _header(self.REQUEST.RESPONSE)
        
        if self.session_on():
            formdata["session"] = self.REQUEST.SESSION
        
        #if self.mode_function_name():
        #    mode = self.mode_function_name()
        #else:

        mode = formdata.get("mode", self.mode_function_name())

        function = self.mode_function(mode)
        
        ret = function(*args, **formdata)

        # dispose any uncommitted transactions from the current ds
        # that hace not been commited.
        if ds is not None:
            ds.rollback()
        
        return ret

    def session_on(self):
        """
        Return True if this adapter provied the mode functions with a
        session object
        """
        return self._session_on

    def path_variables_on(self):
        """
        Accessor.
        """
        # use getattr() to ensure backward compatibility
        # (I'd hate to redo all these objects! ;-)
        return getattr(self, "_path_variables_on", False)

    def path_variables(self):
        """
        Accessor.
        """
        # use getattr() to ensure backward compatibility
        # (I'd hate to redo all these objects! ;-)
        return join(getattr(self, "_path_variables", []), "/")

    def module_name(self):
        """
        Accessor. Return the name of the Python module where the
        mode function resides.
        """
        return self._module_name
    
    def mode_function_name(self):
        """
        Accessor. Return the name of the mode function.
        """
        return self._mode_function_name

    def db_connection_name(self):
        """
        Return the name of the databse connection used for this
        mode.
        """
        return self._db_connection_name

    def db_charset(self):
        """
        Accessor.
        """
        return self._db_charset

    def _ds(self):
        """
        Return an ORM datasource object or None if self._db_connection_name
        is not set.
        """
        if self._db_connection_name:
            # FIXME: Currently this only works with PostgreSQL.
            # We need to figure out a way of telling what kind of
            # database connection we're dealing with so we know what
            # kind of orm.datasource we need to create.
            
            ds = zpsycopg_db_conn(self.aq_parent,
                                  self.db_connection_name(),
                                  self.db_charset())
            return ds
        else:
            return None

    def module(self):
        """
        Return the module object of the modes module
        """
        module = getattr(self, "_v_module", None)
        if module is None:
            name = self.module_name()
            try:
                module = __import__(name, globals(), locals(),
                                    split(name, ".")[1:])
                
                # Save the modification time of the file, the module
                # is loaded from
                if DevelopmentMode:
                    self._v_module_mtime = self._module_mtime(module)
                    
            except ImportError, e:
                msg = "Error importing module %s: %s" % (name, str(e))
                raise NoSuchModule(msg)
                
            self._v_module = module
        else:
            # If the file the module has been loaded from has been modified
            # reload the module and reset the mode functions dict.
            if DevelopmentMode:
                
                # print >> sys.stderr, "Module modification times", self._v_module_mtime, self._module_mtime(self._v_module)
                
                if self._v_module_mtime != self._module_mtime(self._v_module):
                    print >> sys.stderr, "reloading ", self._v_module
                    reload(self._v_module)
                    self._v_module_mtime = self._module_mtime(self._v_module)
                    self._v_mode_functions = {}

                # A modes module may provide a special function,
                # __reload__(), which is called each time we reload the
                # module. It may then reload modules the mode module
                # is depending on. Use with care and watch recursion ;-)
                #
                # This calles for a generic mechanism to reload modules
                # on demand i.e. when they have been modified.
                reload_function = getattr(self._v_module, "__reload__",
                                          None)
                if reload_function is not None:
                    reload_function()
                

        return self._v_module

    def mode_function(self, name=None):
        """
        Return the mode_function function object
        """
        if name is None: name = self.mode_function_name()
        
        # Perform a check of the module's source file date if in
        # development mode
        if DevelopmentMode: self.module()

        functions_dict = getattr(self, "_v_mode_functions", {})

        if functions_dict.has_key(name):            
            return functions_dict[name]
        else:
            module = self.module()
            if not module.__dict__.has_key(name):
                msg = "No Such function %s:" % (name)
                raise NoSuchFunction(msg)
            else:
                functions_dict[name] = module.__dict__[name]

            self._v_mode_functions = functions_dict
            return functions_dict[name]


    def _module_mtime(self, module):
        """
        Return the modification time of the module's source(!) file.
        The time is returned as the number of seconds since the epoch.
        """
        module_file = module.__file__

        # look at the .py file instead of .pyc
        parts = split(module_file, ".")
        fname = join(parts[:-1], ".")
        try:
            py_file = fname + ".py"
            py_mtime = os.stat(py_file).st_mtime
        except OSError:
            py_mtime = 0

        try:
            pyc_file = fname + ".pyc"
            pyc_mtime = os.stat(pyc_file).st_mtime
        except OSError:
            pyc_mtime = 0

        return max(py_mtime, pyc_mtime)

        
    def __before_publishing_traverse__(self, object, REQUEST):
        if self.path_variables_on():
            # if one of our mathods is called ...
            if len(REQUEST.path) > 0 and \
                   hasattr(object, REQUEST.path[0]):
                return
            else:
                path = REQUEST.path[:] # a copy of the path. With the current
                                       # implementation of Zope this is not
                                       # necessary, but just in case the Zope
                                       # team changes things...
                                       # See: BaseRequest.traverse() method

                for variable in self._path_variables:
                    try:
                        value = path.pop()
                        try:
                            value = unicode(value)
                        except UnicodeDecodeError:
                            try:
                                value = unicode(value, "iso-8859-1")
                            except UnicodeDecodeError:
                                value = unicode(repr(value))
                                
                        REQUEST.set(variable, value)
                    except IndexError: # IndexError: pop from empty list
                        pass

                # Stop traversal of the path
                REQUEST['TraversalRequestNameStack'] = []

    def index_html(self, *args, **kw):
        "Just call self"
        return self(*args, **kw)

    def PUT(self, *args, **kw):
        "Just call self"
        return self(*args, **kw)
