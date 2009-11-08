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
# $Log: __init__.py,v $
# Revision 1.5  2006/08/30 03:56:41  t4w00-diedrich
# Added file_as_buffer class.
#
# Revision 1.4  2006/08/29 20:05:58  t4w00-diedrich
# The whole composition and parsing process of the DSC module has been
# changed. Things are a lot more simple now and work much more reliably.
# Documents are encoded in-memory, with imports performed 'lazily', that
# is, on writing. This is a good compromise between speed and memory usage.
#
# Revision 1.3  2006/08/23 12:39:28  t4w00-diedrich
# Merge actually works pretty well now.
#
# Revision 1.2  2006/08/21 18:58:53  t4w00-diedrich
# Added measure module.
#
# Revision 1.1  2006/08/19 15:42:59  t4w00-diedrich
# Initial commit (as util)
#
#
#

"""
Utility classes and functions. Imports the main interface from its
child modules. Ideally this is the only interface you need to these
modules; except for the misc module from which every identifyer is
imported here.
"""

##__all__ = ["", ""]


# misc
from .misc import *

# subfile
from .subfile import subfile

# file_like_buffer
from .file_like_buffer import file_like_buffer, file_as_buffer

# measure
from .measure import *

# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

