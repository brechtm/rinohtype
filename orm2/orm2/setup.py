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
# $Log: setup.py,v $
# Revision 1.5  2006/05/13 17:56:44  diedrich
# orm2a4
#
# Revision 1.4  2006/05/11 15:42:34  diedrich
# orm2a3
#
# Revision 1.3  2006/05/02 13:55:09  diedrich
# Updated for orm2
#
# Revision 1.2  2006/02/25 00:20:20  diedrich
# - Added and tested the ability to use multiple column primary keys.
# - Some small misc bugs.
#
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
#
#

from distutils.core import setup

setup (name = "orm2",
       version = "2a4",
       description = "The Object Relational Membrane v2",
       author = "Diedrich Vorberg",
       author_email = "diedrich@tux4web.de",
       url = "http://orm.nongnu.org/",
       packages = ['orm2', 'orm2.adapters', 'orm2.adapters.pgsql',
                   'orm2.adapters.mysql', 'orm2.adapters.firebird',
                   'orm2.adapters.gadfly', 'orm2.util', 'orm2.ui',
                   'orm2.ui.wrappers'],
       package_dir = {"orm2": "."})


