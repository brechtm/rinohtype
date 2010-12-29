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

from types import *
from ll.xist import xsc

def translate(txt, context):
    """
    Someday soon, this function will return a translation for unicode_string
    suitable for context.

       - If txt is a unicode string it will translate it and return a
         xsc.Text instance to be used with xist
       - If a xist DOM tree is supplied, it will recursively traverse it
         and translate B{all} CharachterData instance's content that are not
         marked with a __translated__ Flag.
         
    """
    if type(txt) == UnicodeType:
        # insert actual translation here!!

        ret = xsc.Text(txt)
        ret.__translated__ = True
        return ret
    
    elif type(txt) == StringType:
        return translate(unicode(txt), context)
    
    elif isinstance(txt, xsc.Text):
        if getattr(txt, "__translated__", False):
            return txt
        else:
            return translate(txt.content, context)

    elif isinstance(txt, xsc.Frag):
        for index, a in enumerate(txt):
            txt[index] = translate(txt[index], context)
            
    elif isinstance(txt, xsc.Element):
        txt.content = translate(txt.content, context)
        
    else:
        tpl = ( repr(type(txt)), repr(txt), )
        raise TypeError("translate can only operate on unicode strings, "+ \
                        "xsc.Element, or xsc.Frag, not %s %s" % tpl)
                            
def translate_template(context, template, *args, **kw):
    """
    The i18n version of the % opperator: template must be a unicode string,
    which will be translated (including the placeholders) and then applied to
    the data passed as either positional arguments or key word arguments.

    Example::

       >>> translate_template(context, '%s %s', one, two)
       '<content of one> <content of two>'
       >>> translate_template(context, '%(one)s %(two)s', one='1', two='2')
       '1 2'

       
    """
    if type(template) == UnicodeType: template = unicode(template)
    
    if type(template) != UnicodeType:
        raise TypeError("tramslate_template can only operate on unicode " + \
                        "strings, not %s %s" % ( repr(type(template)),
                                                 repr(template), ))
    char_data = translate(template)

    if args:
        char_data.content = char_data.content % args
    elif kw:
        char_data.content = char_data.content % kw
    else:
        raise ValueError("You must either supply positional or key words " + \
                         "arguments for the % opperator to work on!")

    return char_data

_ = translate

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

