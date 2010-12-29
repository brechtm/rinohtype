#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

##  This file is part of orm, The Object Relational Membrane.
##
##  Copyright 2002-2004 by Diedrich Vorberg <diedrich@tux4web.de>
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
##  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
##  I have added a copy of the GPL in the file COPYING

# Changelog
# ---------
#
# $Log: __init__.py,v $
# Revision 1.2  2006/10/07 22:08:29  diedrich
# Added ORMProcedure class.
#
# Revision 1.1  2006/06/09 15:37:39  diedrich
# Initial commit
#
# Revision 1.2  2004/08/02 23:05:35  t4w00-diedrich
# Added OEMFSPageTemplate.
#
# Revision 1.1  2004/08/01 15:44:02  t4w00-diedrich
# Initial commit.
#
#
#

import ORMProcedureModule
import ORMProcedure

def initialize(context):
    context.registerClass(
        ORMProcedureModule.ORMProcedureModule,
        permission='Add ORM Procedure Module',
        constructors=(ORMProcedureModule.manage_addORMProcedureModuleForm,
                      ORMProcedureModule.manage_addORMProcedureModule),)
    context.registerBaseClass(ORMProcedureModule.ORMProcedureModule)

    context.registerClass(
        ORMProcedure.ORMProcedure,
        permission='Add ORM Procedure',
        constructors=(ORMProcedure.manage_addORMProcedureForm,
                      ORMProcedure.manage_addORMProcedure),)
    context.registerBaseClass(ORMProcedure.ORMProcedure)

