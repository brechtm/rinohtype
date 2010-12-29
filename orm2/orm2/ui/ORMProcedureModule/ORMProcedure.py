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
#
# $Log: ORMProcedure.py,v $
# Revision 1.6  2007/01/22 19:44:54  diedrich
# - ORMProcedure is a PropertyManager now.
# - Raise an exception if moduel or procedure is None (i.e. there was a syntax error)
#
# Revision 1.5  2006/10/10 15:49:14  diedrich
# - Opt in procedure parameters. (3) Oink!
# - Fixed datetime handling. OinkOink!
#
# Revision 1.4  2006/10/10 15:21:29  diedrich
# Opt in procedure parameters. (2)
#
# Revision 1.3  2006/10/10 15:19:43  diedrich
# Opt in procedure parameters.
#
# Revision 1.2  2006/10/08 15:27:01  diedrich
# Made security measures work.
#
# Revision 1.1  2006/10/07 22:07:34  diedrich
# Initial commit.
#
#
#



# Python
import sys, os, re, imp, urllib
from string import split, join
from types import *
from cStringIO import StringIO
from traceback import print_tb

# Zope
from Acquisition import Implicit, Acquired
from Persistence import Persistent
from AccessControl.Role import RoleManager
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import Item
from OFS.PropertyManager import PropertyManager
from Globals import MessageDialog, DevelopmentMode
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from App.Management import Navigation
from OFS.Cache import Cacheable
from OFS.Folder import Folder

# orm
from orm2.adapters.pgsql.datasource import zpsycopg_db_conn
import orm2.debug
from orm2.ui.procedure import procedure as orm2_ui_procedure

if DevelopmentMode:
    orm2.debug.debug.verbose = True
    orm2.debug.sqllog.verbose = True

class ORMModeException(Exception): pass
class NoSuch(ORMModeException): pass
class NoSuchProcedure(ORMModeException): pass

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

doc_string_param_re=re.compile(r'@param\s*(.*?)\s*:')

def manage_addORMProcedure(self, id,
                           model_name, procedures_name, class_name,
                           db_connection_name, session_on=False,
                           REQUEST=None):
    """
    Add an ORMMode Object to the current Zope instance
    """
    id = str(id)
    model_name = str(model_name)
    procedures_name = str(procedures_name)
    class_name = str(class_name)
    db_connection = str(db_connection_name)

    if str(session_on) == "on":
        session_on = True
    else:
        session_on = False
        
    obj = ORMProcedure(id, model_name, procedures_name, class_name,
                       db_connection_name, REQUEST)
    self._setObject(id, obj)

    if REQUEST is not None:
        #print self, repr(self.absolute_url())
        REQUEST.RESPONSE.redirect(self.absolute_url() + "/%s/manage_form"%id)
        return None
        # return self.manage_form(self, REQUEST)

class module_container(Persistent):
    def __init__(self, name):
        self.module_name = str(name)
        self.last_error = None
        
    def module(self):
        if not hasattr(self, "_v_module") or DevelopmentMode:
            imp.acquire_lock()
            try:
                parts = split(self.module_name, ".")

                path = None
                name = []
                for package in parts[:-1]:
                    name.append(package)
                    file, filename, description = imp.find_module(package,
                                                                  path)
                    module = imp.load_module(join(name, "."),
                                             file, filename,
                                             description)
                    path = module.__path__

                file, filename, description = imp.find_module(parts[-1],
                                                              path)
            
                self._v_module = imp.load_module(self.module_name, file,
                                                 filename, description)

                sys.modules[self.module_name] = self._v_module
                self.last_error = []
                
            except Exception, e:
                self._v_module = None
                exception, desc, traceback = sys.exc_info()
                f = StringIO()
                print_tb(traceback, file=f)
                traceback = f.getvalue()

                print >> sys.stderr, "-" * 60
                print traceback
                print exception
                print desc
                print >> sys.stderr, "-" * 60

                # remove the first two lines of the traceback, which always
                # point to line 140 above. To debug the import mechanism itself
                # this must probably be commented out.
                #lines = split(traceback, "\n")
                #if len(lines) > 2:
                #    traceback = join(lines[2:], "\n")
                #    lines.append("")
                
                self.last_error = [ exception, desc, traceback, ]
            #except:
            #    imp.release_lock()
            #    raise

            imp.release_lock()
            
            if hasattr(self._v_module, "__reload__"):
                self._v_module.__reload__()

            if hasattr(self._v_module, "__relationships__"):
                self._v_module.__relationships__(self._v_module)

        return self._v_module
            



    def set_name(self, name):
        self.module_name = name
        self.last_error = None
        
        if hasattr(self, "_v_module"):
            del self._v_module
    

manage_addORMProcedureForm = PageTemplateFile(
    "www/ORMProcedure.pt", globals())

class ORMProcedure(Item, Implicit, Cacheable, Persistent, PropertyManager):
    """
    This object type allows you to call ORM 'mode' functions from within
    your Zope application.
    """

    meta_type = "ORM Procedure"
    manage_form = PageTemplateFile("www/ORMProcedure.pt", globals())

    manage_options = (
        ( {"label": "Edit", "action": "manage_form"},) + 
        Item.manage_options +
        Cacheable.manage_options +
        RoleManager.manage_options +
        PropertyManager.manage_options )

    ZopeTime=Acquired
    HelpSys=Acquired    

    security = ClassSecurityInfo()

    def __init__(self, id, model_name, procedures_name, class_name,
                 db_connection_name, session_on,
                 REQUEST=None):
        self.id = id
        self.manage_edit(model_name, procedures_name, class_name,
                         db_connection_name, session_on)
        
    security.declareProtected("Change External Methods", 'manage_edit')
    def manage_edit(self, model_name, procedures_name, class_name,
                    db_connection_name, session_on,
                    REQUEST=None):
        """
        Modify the ORMMode object.
        """

        self._model = module_container(model_name)
        self._procedures = module_container(procedures_name)
                
        self._model.module() # To trigger any error message load the module
        self._procedures.module()

        self._class_name = class_name
        
        self._db_connection_name = str(db_connection_name)
        self._session_on = str(session_on)

        if REQUEST is not None:
            message="ORM Procedure updated."
            return self.manage_form(self, REQUEST, manage_tabs_message=message)


    security.declareProtected("View", 'index_html')
    def index_html(self, *args, **kw):        
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

    __call__ = index_html
        

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
            if not unwanted_request_keys.has_key(key):
                value = self.REQUEST[key]

                # convert to Unicode 
                if type(value) == StringType:
                    try:
                        value = unicode(value, encoding)
                    except UnicodeDecodeError:
                        pass
                    
                formdata[key] = value

        ds = self._ds()

        # put together the stuff needed by the mode functions    
        formdata["ds"] = ds
        formdata["base_url"] = self.absolute_url()
        formdata["request"] = self.REQUEST
        formdata["response"] = self.REQUEST.RESPONSE
        formdata["REQUEST"] = self.REQUEST
        formdata["RESPONSE"] = self.REQUEST.RESPONSE
        formdata["context"] = self
        
        if self.session_on():
            formdata["session"] = self.REQUEST.SESSION
        
        #if self.mode_function_name():
        #    mode = self.mode_function_name()
        #else:

        model = self._model.module()
        formdata["model"] = model
        
        procedure_class = self._procedure_class(formdata)

        if procedure_class is None:
            raise Exception("Illegal method name!")
        
        procedure_instance = procedure_class(self, formdata)

        if hasattr(procedure_class, "__call_param_names__"):
            param_names = procedure_class.__call_param_names__
        elif procedure_instance.__call__.__doc__ is not None:
            doc = procedure_instance.__call__.__doc__
            param_names = doc_string_param_re.findall(doc)
            procedure_class.__call_param_names__ = param_names
        else:
            param_names = []

        kw = {}
        if param_names != []:
            for param_name in param_names:
                if formdata.has_key(param_name):
                    kw[param_name] = formdata[param_name]
                    
        try:
            ret = procedure_instance(**kw)
        except:
            if ds is not None: ds.rollback()
            raise

        # dispose any uncommitted transactions from the current ds
        # that have not been commited.
        if ds is not None: ds.rollback()
        
        return ret

    def _procedure_class(self, formdata):
        module = self._procedures.module()
        if module is None:
            raise Exception("module is None")
        
        procedure_class = getattr(module, self._class_name, None)
        if procedure_class is None:
            raise Exception("Procedure_class is None.")
        
        return procedure_class

    
    def session_on(self):
        """
        Return True if this adapter provied the mode functions with a
        session object
        """
        return self._session_on

    def model_name(self):
        """
        Accessor. Return the name of the Python module where the
        mode function resides.
        """
        return self._model.module_name

    def model_error(self):
        """
        Return the exception text of the last error loading the model module,
        otherwise an empty string.
        """
        return self._model.last_error

    def procedures_name(self):
        """
        Accessor. Return the name of the Python module with the
        procedures in it.
        """
        return self._procedures.module_name
    
    def procedures_error(self):
        """
        Return the exception text of the last error loading the procedures
        module, otherwise an empty string.
        """
        return self._procedures.last_error
    
    def class_name(self):
        """
        Return the class name
        """
        return self._class_name
    
    def db_connection_name(self):
        """
        Return the name of the databse connection used for this
        mode.
        """
        return self._db_connection_name

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
            
            ds = zpsycopg_db_conn(self, self.db_connection_name())
            return ds
        else:
            return None
        

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

    def index_html(self, *args, **kw):
        "Just call self"
        return self(*args, **kw)

    def procedure_url(self, procedure_name, **kw):
        """
        Return an absolute_url to this object + procedure_name + params in kw
        """
        if not hasattr(self._procedures.module(), procedure_name):
            raise Exception("Illegal procedure name: %s" % procedure_name)

        for name, value in kw.items():
            if type(value) == UnicodeType:
                kw[name] = value.encode()

        params = urllib.urlencode(kw)

        if params:
            params = "?" + params
        else:
            params = ""

        url = "%s/%s%s" % ( self.absolute_url(), procedure_name, params, )

        return url
                          

