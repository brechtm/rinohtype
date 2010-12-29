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
##  I have added a copy of the GPL in the file COPYING

# Changelog
# ---------
#
# $Log: debug.py,v $
# Revision 1.6  2006/05/13 17:23:42  diedrich
# Massive docstring update.
#
# Revision 1.5  2006/04/28 09:49:27  diedrich
# Docstring updates for epydoc
#
# Revision 1.4  2006/04/15 23:19:32  diedrich
# Added reset() method to sql log class.
#
# Revision 1.3  2005/12/31 18:28:05  diedrich
# - Updated year in copyright header ;)
#
# Revision 1.2  2005/12/18 22:35:46  diedrich
# - Inheritance
# - pgsql adapter
# - first unit tests
# - some more comments
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
#
#

__docformat__ = "epytext en"

"""
orm's debug module was re-written in one of my brigher moments:

First of all it contains a class called _logstream which implements a
subset of Python's file interface. This class is instantiated three
times and the objects are provided as global variables: log, debug and
sql. Each of these have a verbose attribute which determines, it log,
debug or sql information are written to stderr.

Furthermore, the _logstream class contains a mechanism to
automatically add options to a Python optparse.option_parser
automatically. Example:

    >>> parser = optparse.OptionParser(doc, version=__version__)
    >>> log.add_option(parser)
    >>> debug.add_option(parser)

resulting in these options:

  -v, --verbose         Be verbose (to stderr)
  -d, --debug           Print debug messages (to stderr)

sql only adds a long --show-sql option if used in this manner. If
you'd like to use other switches you'll have to copy the lines below
over to your program.

"""

import sys
from string import *


class _logstream:
    """    
    Implement a subset of the file interface to be used for status
    messages.  Depending on its verbose flag, the write() method will
    pass its argument to sys.stderr.write() or discard it.
    """
    def __init__(self):
        self.verbose = False
        
    def write(self, s):
        if self.verbose:
            sys.stderr.write(s)

    def flush(self):
        if self.verbose:
            sys.stderr.flush()

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
        
class _sql(_logstream):
    """
    The _sql class has a logging mechanism that is controlled through
    the buffer_size attribute. If buffer_size is greater than 0, buffer_size
    sql statements will be retained in a list attribute called queries. This
    is used by unit tests to see if queries are generated as expected.
    """
    
    def __init__(self):
        _logstream.__init__(self)
        self.buffer_size = 0
        self.queries = []
        
    def write(self, s):
        _logstream.write(self, s)

        s = strip(s)
        if s == "": return

        if self.buffer_size > 0:
            self.queries.append(s)
            if len(self.queries) > self.buffer_size:
                del self.queries[0]

    def reset(self):
        self.queries = []
        
    def add_option(self, option_parser):
        option_parser.add_option("--show-sql", action="callback",
                                 callback=self,
                                 help="Log SQL queries and commands (to stderr)")
        
log = _log()
debug = _debug()
sqllog = _sql()
