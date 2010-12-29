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
# $Log: validators.py,v $
# Revision 1.7  2006/07/08 17:09:40  diedrich
# Changed email and domain regex to contain ^ and $
#
# Revision 1.6  2006/07/05 21:42:37  diedrich
# - Added not_empty_validator
# - Several validators didn't handle None values as expected, fixed that
#
# Revision 1.5  2006/07/04 22:45:44  diedrich
# Import string
#
# Revision 1.4  2006/05/13 17:23:41  diedrich
# Massive docstring update.
#
# Revision 1.3  2006/04/28 09:49:26  diedrich
# Docstring updates for epydoc
#
# Revision 1.2  2006/04/28 08:45:11  diedrich
# Added validators.
#
# Revision 1.1  2006/04/21 18:55:10  diedrich
# Initial commit
#
#

"""
This module defines classes for validating values stored in dbproperties
before they screw up the database or cause a CONSTRAINT error.
"""


import re
from types import *
from string import *
from orm2.exceptions import *

class validator:
    """
    The default validator: It doesn't check anything.
    """
    def check(self, dbobj, dbproperty, value):
        return True

class not_null_validator(validator):
    """
    For NOT NULL columns.
    """
    def check(self, dbobj, dbproperty, value):
        if value is None:
            tpl = ( dbobj.__class__.__name__,
                    dbproperty.attribute_name, )
            raise NotNullError("%s.%s may not be NULL (None)" % tpl,
                               dbobj, dbproperty, value)


not_none_validator = not_null_validator # which identifyer makes more sense??

class not_empty_validator(validator):
    """
    For columns which may not contain empty strings.
    """
    def check(self, dbobj, dbproperty, value):
        if type(value) == StringType or type(value) == UnicodeType:
            if value == "":
                tpl = ( dbobj.__class__.__name__,
                        dbproperty.attribute_name, )
                raise NotEmptyError("%s.%s may not be empty" % tpl,
                                    dbobj, dbproperty, value)

class length_validator(validator):
    """
    Check an argument value's length. None values will be ignored.
    """
    def __init__(self, max_length):
        self.max_length = max_length
        
    def check(self, dbobj, dbproperty, value):
        if value is not None and len(value) > self.max_length:
            msg = "Length check failed on %s.%s" % (dbobj.__class__.__name__,
                                                    dbproperty.attribute_name,)
            raise LengthValidatorException(msg, dbobj, dbproperty, value)

class range_validator(validator):
    """
    A generic validator for value ranges (fortunately Python doesn't care, it
    can be used for numerals, dates, strings...)
    """
    def __init__(self, lo, hi, include_bounds=False):
        """
        The formula goes::

           lo < value < hi

        if include_bounds is False (the default) or::

           lo <= value <= hi

        otherwise. If above formula is not valid, a RangeValidatorError will
        be raised by check()
        """
        self.lo = lo
        self.hi = hi
        self.include_bounds = include_bounds

    def check(self, dbobj, dbproperty, value):
        if not self.include_bounds:
            if self.lo < value and value < self.hi:
                return
            else:
                message = "Unmatched condition: %s < %s < %s (%s.%s)"
        else:
            if self.lo <= value and value <= self.hi:
                return
            else:
                message = "Unmatched condition: %s <= %s <= %s (%s.%s)"

        tpl = ( repr(self.lo), repr(self.hi), repr(value),
                dbobj.__class__.__name__, dbproperty.attribute_name, )
        raise RangeValidatorException(message % tpl, dbobj, dbproperty, value)

class re_validator(validator):
    """
    Regular expression validator. For strings and Unicode Objects
    """
    def __init__(self, re):
        if type(re) in ( StringType, UnicodeType, ):
            self.re = re.compile(re)
        else:
            self.re = re

    def check(self, dbobj, dbproperty, value):
        match = self.re.match(value)

        if match is None:
            tpl = ( repr(value), self.re.pattern,
                    dbobj.__class__.__name__, dbproperty.attribute_name, )
            msg = "%s does not match regular expression %s (%s.%s)" % tpl
            raise ReValidatorException(msg, dbobj, dbproperty, self.re, value)


# some usefull validators for standard situations #########################


# regular expressions that may proof usefull 
domain_name_re = re.compile("^([0-9a-z]([0-9a-z-]*[0-9a-z])?\.)+[a-z]{2,4}$")
local_part_re = re.compile(r"^[-a-z0-9_\.]+$")
email_re = re.compile("^[-a-z0-9_\.]+@([0-9a-z]([0-9a-z-]*[0-9a-z])?\.)+[a-z]{2,4}$")

class email_validator(re_validator):
    """
    Check if the value is a valid e-Mail Address using a regular expression.
    Note that the re will not match un-encoded idna Domains, but it will work
    on Unicode strings.
    """
    
    def __init__(self):
        re_validator.__init__(self, email_re)

class fqdn_validator(re_validator):
    """
    Check if the value is a valid fully qualified domain name. Note
    that the rgex used will not match un-encoded idna Domains.
    """
    
    def __init__(self):
        re_validator.__init__(self, domain_name_re)

class idna_fqdn_validator(fqdn_validator):
    """
    Like fqdn_validator above, but for idna Domains (Unicode)
    """
    def check(self, dbobj, dbproperty, value):
        if value is None:
            return
        
        if type(value) != UnicodeType:
            raise TypeError("An idna fqdn must be represented as a " + \
                            "unicode string!")
        
        value = value.encode("idna")
        fqdn_validator.check(self, dbobj, dbproperty, value)


class idna_email_validator(email_validator):
    """
    Like email_validator above, but for idna Domains (Unicode)
    """

    def check(self, dbobj, dbproperty, value):
        if value is None:
            return
        
        if type(value) != UnicodeType:
            raise TypeError("An idna fqdn must be represented as a " + \
                            "unicode string!")

        parts = split(value, "@")
        if len(parts) == 2:
            local_part, remote_part = parts

            try:
                local_part = local_part.encode("ascii")
            except UnicodeDecodeError:
                msg = "The local part of an e-mail address may not contain "+\
                      "non-ascii characters! (Even for an idna Domain!)"
                raise ReValidatorException(msg, dbobj, dbproperty,
                                           self.re, value)
            
            remote_part = remote_part.encode("idna")

            email_validator().check(dbobj, dbproperty,
                                    local_part + "@" + remote_part)
        else:
            tpl = ( repr(value), self.re.pattern,
                    dbobj.__class__.__name__, dbproperty.attribute_name, )
            msg = "%s does not match regular expression %s (%s.%s)" % tpl
            raise ReValidatorException(msg, dbobj, dbproperty, self.re, value)

        
        
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

