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

"""
 
"""

from orm2.ui import widget, view
from orm2.exceptions import ValidatorException

from i18n import translate, _

from ll.xist.ns import xml, html, chars


class xist_view(view):
    def __getattr__(self, name):
        if not hasattr(self, "context"):
            self.context = self.ds().context

            if name == "context":
                return self.context
            
        return getattr(self.context, name)

class xist_form(xist_view):
    def rows(self):
        """
        Return a list that contains ll.xist.Node objects and _xist_widget
        object. The nodes will be passed into the form as-is, the widgets
        will be initialized according to form usage, either with the values
        from the request+errors (on failed submits), values from the dbobject
        (display for a modification) or the defaults (for a new dbobject).

        This default implementation will return all the widget_specs that
        are xist widgets from the dbclass.
        """
        for widget_spec in self.dbobj.__widget_specs__("xist"):
            yield widget_spec

    def widgets(self):
        """
        Return a list of widgets in this form (i.e. extract the
        instances of widget from the result of (rows).
        """
        rows = self.rows()
        return filter(lambda row: isinstance(row, widget), rows)

    def set_from_request(self, ignore_if_unset=True):
        """
        Call the set_from_request() method of every widget. Catch validator
        exceptions and process them into error messages using the
        error_message() function. Return a dictionary as

           { 'param_name', [ error1, error2, ..., errorn ] }

        An empty dict means successful submition ;-)
        """
        ret = {}
        for widget in self.widgets():
            actual_widget = widget(self.dbobj)

            errors = ret.get(actual_widget.name, [])
            
            try:
                actual_widget.set_from_request(use_default=False,
                                               ignore_if_unset=ignore_if_unset)
            except ValidatorException, e:
                msg = self.error_message(actual_widget, e)
                errors.append(msg)

                ret[actual_widget.name] = errors

        return ret

    def error_message(self, widget, exception):
        """
        Return an error message for when widget raised
        ValidatorException exception. This error message will be
        translated into the user's language by xist.widgets.row()
        if need be.
        """
        return unicode(str(exception))
    
    def __call__(self, errors={}, **kw):
        form = html.form(**kw)
            
        for row in self.rows():
            if isinstance(row, widget):
                actual_widget = row(self.dbobj)
                error = errors.get(actual_widget.name, None)
                form.append(actual_widget.row(error=error))
            else:
                form.append(row)

        return form

        
        


# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

