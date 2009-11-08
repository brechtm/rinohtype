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


import sys
from psg.document.dsc import dsc_document

def print_subsections(section, level=0):
    for subsection in section.subsections():
        print "++" * level, subsection.name
        #subsection.subfile.seek(0)
        #print repr(subsection.subfile.read(30))
        
        print_subsections(subsection, level=level+1),
        

def main():
    fp = open(sys.argv[1], "rb")

    doc = dsc_document.from_file(fp)    

    print
    print "Title:", repr(doc.title)
    print "Pages:", doc.pages
    print "-" * 50
    print
    
    print_subsections(doc)

    print list(doc.resources())

    
    #for a in doc.resources():
    #    print "-" * 50
    #    s = repr(a)
    #    print repr(s)
    #    print repr(a.section.as_string()[:100])
    #    print repr(a.section.as_string()[-100:])
    #    print "-" * 50
        
    #print doc.document_supplied_resources
    #print doc.document_needed_resources

    #print
    #print "Prolog " + "-" * 50
    #print
    #for a in doc.Prolog.subsections():
    #    print a.name




main()
