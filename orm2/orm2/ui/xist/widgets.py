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
# $Log: widgets.py,v $
# Revision 1.9  2007/01/22 19:45:46  diedrich
# Added a parameter to mapping_radiobuttons that determines whether they
# each are in a <div> or not.
#
# Revision 1.8  2006/10/07 22:10:18  diedrich
# Fixed error message handling.
#
# Revision 1.7  2006/09/04 15:58:42  diedrich
# Bug fixing
#
# Revision 1.6  2006/07/08 17:12:56  diedrich
# - added hidden_primary_key class
# - changed checkbox.row()
# - added datetime_input class
#
# Revision 1.5  2006/07/05 21:44:13  diedrich
# - Added utext, mapping_radiobutton
# - Several changed
#
# Revision 1.4  2006/07/04 22:51:23  diedrich
# - Implemented belongs_to() methods
# - Added get_from_result() and set_from_result()
#
# Revision 1.3  2006/06/11 23:48:14  diedrich
# Fixed value()
#
# Revision 1.2  2006/06/10 18:08:17  diedrich
# Rewrote the whole thing to make sense. Introduced widget/actual_widget
# seperation
#
# Revision 1.1  2006/05/15 21:43:31  diedrich
# Initial commit
#
# Revision 1.1  2006/04/28 09:56:41  diedrich
# Initial commit
#
#

import sys, datetime, time
from string import *
from types import *

from orm2.ui import widget
from orm2.validators import *
from orm2 import datatypes

from i18n import translate, _

from ll.xist.ns import html, xml, chars
from ll.xist.xsc import *
from ll.xist import parsers
from ll.xist.errors import NodeNotFoundError


class xist_widget(widget):

    def belongs_to(self, module_name):
        return module_name == "xist"
    
    class actual_widget(widget.actual_widget):
        def __init__(self, dbobj, dbproperty, errors={},
                     name=None, title=None, help="", default=None, **kw):
            """
            @param dbobj: The dbobj whoes property is to be displayed by this
              widget
            @param errors: Dict that contains the error messages from the last
              commit.
            @param name: The name attribute of the HTML <input> (or so) element
              that will be created by this. Defaults to dbclass.attribute,
              which will do for most circumstances... A regular String.
            @param title: Will overwrite the datatype.title attribute for the
              widget's caption. Unicode string required.
            @param help: Help text that will be displayed along with the
              widget. May be a XIST element, of course, but you may not want
              to use block level elements in it.
            @param default: Unicode String or other Python object suitable  to
              determine the default setting for this widget if dbobj is None
              (see widget() below)

            The key word arguments may be used to pass arbitrary
            attributes to the widget element.
            """            
            widget.actual_widget.__init__(self, dbobj, dbproperty)
            self.errors = errors
            
            if name is None:
                self.name = "%s_%s" % ( dbproperty.dbclass.__name__,
                                        dbproperty.attribute_name, )
            else:
                if type(name) != StringType:
                    msg = "HTML name property must be string not %s"%repr(name)
                    raise TypeError(msg)

                self.name = name

            if title is None:
                self.title = translate(self.dbproperty.title, self)
            else:
                self.title = title

            if help is None:
                self._help = Frag()
            else:
                self._help = translate(help, self)

            self.default = default

            self.extra_args = kw

        def widget(self, **kw):
            """
            Returns a xist frag that represents the HTML to create the
            widget.  Ideally this is a single HTML element. The key
            word arguments will be passed as attributes, overwriting
            the constructor's key word arguments (see above).
            """
            raise NotImplementedError()

        def help(self, **kw):
            """
            @returns: A html.div instance containing the help
              message. The key word arguments will be added to the <div>
              as arguments. The css class defaults to 'help'
            """
            if not kw.has_key("class_"):
                kw["class_"] = "help"

            if self._help:
                return html.div(self._help, **kw)
            else:
                return Frag()

        def label(self, **kw):
            """
            @returns: A html.div instance containing the widget's label
              (title attribute). The key word arguments will be added to the
              <div> as arguments. The css class defaults to 'label'
            """    
            if not kw.has_key("class_"):
                kw["class_"] = "label"

            required = False
            for validator in self.dbproperty.validators:
                if isinstance(validator, not_null_validator) or \
                   isinstance(validator, not_empty_validator):
                    required = True
                    break

            if required:
                kw["class_"] += " required"

            return html.div(self.title, **kw)

        def error_message(self, error):
            '''
            Return a <div class="error"> with the formated error
            message in it.
            '''
            if error is not None:
                if type(error) in (ListType, TupleType,):
                    if len(error) > 1:
                        ul = html.ul()
                        for e in error:
                            ul.append(html.li(translate(e, self)))

                        error = ul
                    else:
                        error = translate(error[0], self)
                else:
                    error = translate(error, self)

                error = html.div(error, class_="error")
                    
                return error
            else:
                return Frag()

        def row(self, plone=False, error=None, **kw):
            '''
            Return a row for an HTML form

            <div class="row">
              <div class="label">self.title</div>
              <div class="help">self._help if non-null</div>
              <div class="error">error if non-null</div>

              <div class="field">
                self.widget()
              </div>
            </div>

            @param plone: Set attributes so that this form may be used with
              CMFPlone`s JavaScript (unimplemented)
            @param error: Error message to be displayed along with the widget.
            '''
            return html.div(self.label(), self.help(),
                            self.error_message(error),
                            html.div(self.widget(**kw), class_="field"),
                            class_="row")

        def value(self):
            """
            If the current request contains a value for our form element's
            name, return that value, otherwise get it from the dbobj. If
            that should fail, return the default.
            """
            try:
                ret = self.get_from_request(use_default=False)
            except KeyError:
                if self.dbproperty.isset(self.dbobj):
                    ret = self.dbproperty.__get__(self.dbobj)
                else:
                    ret = self.default

            return ret

        def get_from_request(self, use_default=False):
            """
            Check the request for a parameter with this widget's name
            attribute. It it is set return it as is. Otherwise return
            the default value (if use_default is True) or raise
            KeyError.
            """
            REQUEST = self.REQUEST
            
            if REQUEST.has_key(self.name):
                return REQUEST[self.name]
            else:
                if use_default:
                    return self.default
                else:
                    raise KeyError("REQUEST does not contain %s param" % \
                                      self.name)

        def set_from_request(self, use_default=False, ignore_if_unset=False):
            """
            The the dbattribute this widget is responsible for from REQUEST
            (using L{get_from_request} above).

            @param REQUEST: Zope request object (or any other dict for that
               matter)
            @param use_default: Use this widget's default value if the REQUEST
               does not contain an appropriate value.
            @raises: KeyError if the REQUEST does not contain an appropriate
               value.
            """
            try:
                self.dbproperty.__set__(self.dbobj,
                                        self.get_from_request(False))
            except KeyError:
                if ignore_if_unset:
                    pass
                else:
                    raise
            
        
        def __getattr__(self, name):
            """
            Since this class is used almost exclusively inside Zope,
            this will hook it into Zope's acquisition mechanism.
            """
            if not hasattr(self, "context"):
                self.context = self.dbobj.__ds__().context
            if name == "context": return self.context

            return getattr(self.context, name)


        
class _input(xist_widget):    
    '''
    Base class for <input /> element based widgets. The type= attribute is
    determined by the class name.
    '''
    class actual_widget(xist_widget.actual_widget):
        def widget(self, **kw):
            extra_args = self.extra_args.copy()
            extra_args.update(kw)
            
            return html.input(type=self.type,
                              value=self.value(),
                              name=self.name, **extra_args)


class text(_input):
    """
    
    """
    def __init__(self, empty_to_none=False, **kw):
        """
        @param mapping: A list of pairs as ( 'identifyer', u'title', ) that
           will be used to create the widget.
        @param sort: Boolean value that determins if the mapping will be
           sorted by its title component before any HTML is created from it.
        """
        xist_widget.__init__(self, **kw)
        self.empty_to_none = empty_to_none

    def __call__(self, dbobj, **kw):
        params = self.params.copy()
        params.update(kw)

        return self.actual_widget(dbobj, self.dbproperty,
                                  self.empty_to_none, **params)
    
    class actual_widget(_input.actual_widget):
        type = "text"
        
        def __init__(self, dbobj, dbproperty, empty_to_none, **kw):
            _input.actual_widget.__init__(self, dbobj, dbproperty, **kw)
            self.empty_to_none = empty_to_none
        
        def value(self):
            u = xist_widget.actual_widget.value(self)
            
            if u is None:
                return u""
            elif type(u) != UnicodeType:
                u = unicode(u)
                
            return u

        def get_from_request(self, use_default=False):
            """
            Check the request for a parameter with this widget's name
            attribute. It it is set return it as is. Otherwise return
            the default value (if use_default is True) or raise
            KeyError.
            """
            if self.REQUEST.has_key(self.name):
                ret = self.REQUEST[self.name]

                if ret == "" and self.empty_to_none:
                    return None
                else:
                    return ret
            else:
                if use_default:
                    return self.default
                else:
                    raise KeyError("REQUEST does not contain %s param" % \
                                      self.name)
                
class utext(text):
    """
    This widget will enforce that the object handled is a unicode string
    (rather than attempting to cast it into one like text does).
    """

    class actual_widget(text.actual_widget):
        type = "text"
        
        def value(self):
            u = text.actual_widget.value(self)
            
            if u is None:
                return u""
            elif type(u) != UnicodeType:
                msg = "dbattributes managed by a %s.%s widget must " + \
                      "return a Unicode object! (%s.%s returned %s)"
                msg = msg % ( self.__class__.__module__,
                              self.__class__.__name__,
                              self.dbobj.__class__.__name__,
                              self.dbproperty.attribute_name,
                              repr(u), )
                raise TypeError(msg)
            
            return u

        def get_from_request(self, use_default=False):
            u = text.actual_widget.get_from_request(self, use_default)

            request_charset = "utf-8"
            
            if u is not None:
                u = unicode(u, request_charset)
                
            return u

class hidden(text):
    class actual_widget(text.actual_widget):
        type = "hidden"
        
        def row(self, plone=False, error=None, **kw):
            return self.widget(**kw)

class hidden_primary_key(hidden):
    """
    Special hidden widget for primary keys. The set_from_request() method
    does nothing, because this doesn't make sense for primary keys.
    """
    class actual_widget(hidden.actual_widget):
        def set_from_request(self, use_default=False, ignore_if_unset=False):
            """
            The primary key is never set.
            """
            pass


class checkbox(_input):
    class actual_widget(xist_widget.actual_widget):
        type = "checkbox"
        
        def widget(self, **kw):
            extra_args = self.extra_args.copy()
            extra_args.update(kw)
            
            value = self.value()
            
            if value:
                checked = "checked"
            else:
                checked = None

            cbid = "check-box-%i" % id(self)
            return html.div(html.input(type="checkbox", checked=checked,
                                       name=self.name, id=cbid),
                            html.label(self.title, for_=cbid),
                            class_="checkbox", **extra_args)

        def label(self, **lw):
            return Frag()

        def row(self, plone=False, error=None, **kw):
            ret = self.widget(**kw)
            ret.insert(0, self.error_message(error))
            ret.append(self.help(**kw))
            return ret
            
    
        def value(self):
            """
            This assumes that forms set either submitted or form_submitted
            on submitb
            """
            if self.REQUEST.has_key("submitted") or \
                   self.REQUEST.has_key("form_submitted"):
                ret = self.get_from_request()
            else:
                if self.dbproperty.isset(self.dbobj):
                    ret = self.dbproperty.__get__(self.dbobj)
                else:
                    ret = self.default

            return bool(ret)
    
        def get_from_request(self, use_default=False):
            """
            Check the request for a parameter with this widget's name
            attribute. It it is set return it as is. Otherwise return
            the default value (if use_default is True) or raise
            KeyError.
            """
            return self.REQUEST.has_key(self.name)        
                
class textarea(text):
    class actual_widget(text.actual_widget):
        def widget(self, **kw):
            extra_args = self.extra_args.copy()
            extra_args.update(kw)

            return html.textarea(self.value(), name=self.name, **extra_args)

class utextarea(utext):
    """
    This is analogous for textarea what utext is to text.
    """
    actual_widget = textarea.actual_widget


class mapping_radiobuttons(xist_widget):
    def __init__(self, mapping, sort=False, div=True, **kw):
        """
        @param mapping: A list of pairs as ( 'identifyer', u'title', ) that
           will be used to create the widget.
        @param sort: Boolean value that determins if the mapping will be
           sorted by its title component before any HTML is created from it.
        @param div: Add a <div> around a <input>/<label> pair to position the
          radio buttons vertically. Defaults to True.
        """
        xist_widget.__init__(self, **kw)
        self.mapping = mapping
        self.sort = sort
        self.div = div 

    def __call__(self, dbobj, **kw):
        params = self.params.copy()
        params.update(kw)

        return self.actual_widget(dbobj, self.dbproperty,
                                  self.mapping, self.sort, self.div, **params)

    class actual_widget(xist_widget.actual_widget):
        def __init__(self, dbobj, dbproperty, mapping, sort, div, **kw):
            xist_widget.actual_widget.__init__(self, dbobj, dbproperty, **kw)
            self._mapping = mapping
            self.sort = sort
            self.div = div

        def widget(self, **kw):
            extra_args = self.extra_args.copy()
            extra_args.update(kw)

            ret = html.div(**extra_args)
            current = self.value()
            
            for name, title in self.mapping():
                radio_button_id = "radio-button-%i" % id(name)

                if name == current:
                    checked = 'checked'
                else:
                    checked = None

                button = Frag(html.input(type="radio", name=self.name,
                                         value=name, checked=checked,
                                         id=radio_button_id),
                              html.label(title, for_=radio_button_id))

                if self.div:
                    ret.append(html.div(button, class_="radio-button-row"))
                else:
                    ret.append(button, " ")

            return ret

        def mapping(self):
            mapping = self._mapping

            if self.sort:
                mapping = mapping.sorted(lambda a, b: cmp(a[1], b[1]))

            return mapping
        
class datetime_input(text):
    def __init__(self, format, target_cls=None, empty_to_none=False, **kw):
        """
        @param format: strftime()/strptime() compatible format string (see
           U{http://docs.python.org/lib/module-time.html}
        @param farget_class: Either datetime.date or datetime.datetime. Any
           compatible class (providing a fromtimestamp()
           constructor with the same semantics) will also work. If set to None
           (the default) the class of the dbproperty will determin the class
           used.
        """
        text.__init__(self, empty_to_none, **kw)
        self.format = format
        self.target_cls = target_cls

    def __call__(self, dbobj, **kw):
        params = self.params.copy()
        params.update(kw)

        return self.actual_widget(dbobj, self.dbproperty,
                                  self.empty_to_none,
                                  self.format, self.target_cls,
                                  **params)

    class actual_widget(text.actual_widget):
        def __init__(self, dbobj, dbproperty, empty_to_none,
                     format, target_cls, **kw):
            text.actual_widget.__init__(self, dbobj, dbproperty,
                                        empty_to_none, **kw)
            self.format = format

            if target_cls is None:
                if isinstance(dbproperty, datatypes.datetime):
                    self.target_cls = datetime.datetime
                elif isinstance(dbproperty, datatypes.date):
                    self.target_cls = datetime.date
                else:
                    raise TypeError("You must specify a target_cls for "+\
                                    "datetime_input if it's not used with "+\
                                    "datatype.date or datetime.")
            else:
                self.target_cls = target_cls

            
        def value(self):    
            try:
                v = xist_widget.actual_widget.value(self)
            except DateValidatorException:
                # A date value that can't be pased is re-displayed
                # and fails in the get_from_request() method below.
                # This should probably be done more obviously.
                v = text.actual_widget.get_from_request(self)

            if v is None or v == "":
                return u""
            elif isinstance(v, (datetime.datetime, datetime.date,) ):
                return v.strftime(self.format)
            else:
                if type(v) == UnicodeType:
                    return v
                else:
                    return unicode(v)

        def get_from_request(self, use_default=False):
            s = text.actual_widget.get_from_request(self, use_default)

            if s is None or ( s == "" and self.empty_to_none ):
                return None
            else:
                try:
                    time_t = time.strptime(s, self.format)
                except ValueError:
                    raise DateValidatorException(
                        "Can't parse date %s using (%s) " % (
                                             repr(s), repr(self.format), ),
                        self.dbobj, self.dbproperty, s, self.format)

                try:
                    timestamp = time.mktime(time_t)
                    return self.target_cls.fromtimestamp(timestamp)
                except OverflowError:
                    y, m, d, H, M, S, d1, d2, d3 = time_t
                    if self.target_cls == datetime.datetime:
                        return datetime.datetime(year=y, day=d, month=m,
                                                 hour=H, minute=M, second=S)
                    elif self.target_cls == datetime.date:
                        return datetime.date(year=y, month=m, day=d)
                    else:
                        raise
                        
            
        
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

