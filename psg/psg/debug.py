#!/usr/bin/python
##  This file is part of psg, PostScript Generator.
##
##  Copyright 2006 by Diedrich Vorberg <diedrich@tux4web.de>
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
# $Log: debug.py,v $
# Revision 1.1  2006/08/29 20:04:12  t4w00-diedrich
# Imported from orm
#
#
#

"""

 
"""




__docformat__ = "epytext en"

"""
psg has inherited its debug module from orm, its older brother.

First of all the module contains a class called _logstream which
implements a subset of Python's file interface. This class is
instantiated two times and the objects are provided as global
variables: log and debug. Each of these have a verbose attribute which
determines, it log or debug information are written to stderr.

Furthermore, the _logstream class contains a mechanism to
automatically add options to a Python optparse.option_parser
automatically. Example:

    >>> parser = optparse.OptionParser(doc, version=__version__)
    >>> log.add_option(parser)
    >>> debug.add_option(parser)

resulting in these options:

  -v, --verbose         Be verbose (to stderr)
  -d, --debug           Print debug messages (to stderr)
"""

import sys
from string import *


class _logstream:
    """    
    Implement a subset of the file interface to be used for status
    messages.  Depending on its verbose flag, the write() method will
    pass its argument to sys.stderr.write() or discard it.
    """
    def __init__(self, target=sys.stderr):
        self.verbose = False
        self.target = target
        
    def write(self, s):
        if self.verbose:
            self.target.write(s)

    def flush(self):
        if self.verbose:
            self.target.flush()

    def __call__(self, option, opt, value, parser):
        """
        Called by the Option Parser when the command line option
        added by the add_option method() implemented by the two child
        classes is present.
        """
        self.verbose = True

    def __nonzero__(self):
        """
        Return true if logging is ON, otherwise return False. This is ment
        to be used in if clauses::

           if debug:
              print 'Debug!'
        """
        if self.verbose:
            return True
        else:
            return False
        
        
class _log(_logstream):
    def add_option(self, option_parser):
        option_parser.add_option("-v", "--verbose", action="callback",
                                 callback=self, help="Be verbose (to stderr)")
class _debug(_logstream):
    def add_option(self, option_parser):
        option_parser.add_option("-d", "--debug", action="callback",
                                 callback=self,
                                 help="Print debug messages (to stderr)")
        
log = _log()
debug = _debug()

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:
