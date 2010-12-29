#!/bin/sh

#
# $Log: generate_api_doc.sh,v $
# Revision 1.2  2006/05/13 17:31:06  diedrich
# Added --docformat string
#
# Revision 1.1  2006/04/28 09:48:41  diedrich
# Initial commit
#
#

epydoc -o api --name "Object Relational Membrane (v.2)" \
        --url https://savannah.nongnu.org/projects/orm/ -v orm2
        