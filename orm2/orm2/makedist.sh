#!/bin/bash

# Changelog
# ---------
#
# $Log: makedist.sh,v $
# Revision 1.1.1.1  2005/11/20 14:55:46  diedrich
# Initial import
#
# Revision 3.1  2004/03/26 20:50:08  diedrich
# Added cgi and sql files to the autosearch list
#
# Revision 3.0  2003/09/06 20:04:33  diedrich
# Changed copyright header.
# Added -*- coding -*- for Python 2.3 (for all files now)
#
# Revision 2.0  2002/11/12 22:53:43  diedrich
# *** empty log message ***
#
# Revision 1.2  2002/10/05 17:57:31  diedrich
# No wonder I didn't find any documentation on automatic insertion of Changelog
# messages: it's just too simple to loose a word about it.
#
#

echo -n "Converting documentation..."
cd doc
. ./html.sh
cd ..
echo " done."

cat MANIFEST.in > MANIFEST
find -name "*.py" >> MANIFEST
find -name "*.cgi" >> MANIFEST
find -name "*.sql" >> MANIFEST

./setup.py sdist
