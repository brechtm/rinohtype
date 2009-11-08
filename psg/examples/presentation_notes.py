#!/usr/bin/env python

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


# Changelog
# ---------
#
# $Log: presentation_notes.py,v $
# Revision 1.2  2006/11/04 18:20:39  diedrich
# Docstring update
#
# Revision 1.1  2006/10/29 12:58:33  diedrich
# Initial commit
#
#
#


"""\
NAME

     presentation_notes.py - Create a hardcopy handout of a screen
     presentation that has room for personal notes on it.

SYNOPSIS

     presentation_notes.py [-oout.ps] [-v] [-n thumbs] [-p papersize] input.ps

DESCRIPTION

     This program will create a PostScript document that contains
     'thumb' slides on the left hand side so it gives you room for
     notes.

     If the -o option is used, output will be sent to the file
     specified, otherwise to stdio.

     The -v option will turn on verbose mode.

     The -n option lets you specify how many thumbs are supposed to be
     on one output page. It defaults to 5.

     The -p option lets you specify the paper size and defaults to a4.

"""

import sys, os, optparse
from datetime import datetime

from psg.document.dsc import *
from psg.drawing import box
from psg.util import *
from psg import procsets

def thumb_box_factory(output_document, paper_size_name, margin_width,
                      thumbs_per_page, thumb_width, thumb_height,thumb_spacing,
                      verbose, **kw):
    while True:
        page = output_document.page(page_size=paper_size_name)
        canvas = page.canvas(margin_width, border=False)

        for a in range(thumbs_per_page-1, -1, -1):
            thumb_box = box.canvas(canvas,
                                   0, a * ( thumb_height + thumb_spacing ),
                                   thumb_width, thumb_height,
                                   border=verbose, clipping=True)
            canvas.append(thumb_box)
            yield thumb_box

def main(argv, doc):
    op = optparse.OptionParser(usage=doc)
    op.add_option("-o", None, dest="output_file", default="-",
                  help="Output file")
    op.add_option("-v", None, dest="verbose",
                  action="store_true", default="False",
                  help="Verbose operations")
    op.add_option("-n", None, dest="thumbs_per_page", default="5",
                  help="Thumbs per page. Defaults to 5.")
    op.add_option("-m", None, dest="margin_width", default="25mm",
                  help="Margin width. Defaults to 25mm")
    op.add_option("-s", None, dest="thumb_spacing", default="3mm",
                  help="Thumb spacing. Defaults to 3mm.")
    
    op.add_option("-p", None, dest="output_paper_size", default="a4",
                  help="Output paper size. Defaults to 'a4'")
    
    op.add_option("-P", None, dest="input_paper_size", default="a4landscape",
                  help="Input paper size. Defaults to 'a4landscape'")

    op.add_option("-R", None, dest="rotate", default=False,
                  action="store_true",
                  help="Rotate the input pages 90 deg clockwise.")

    ( options, arguments, ) = op.parse_args()

    if len(arguments) < 1 :
        op.error("Please specify an input file on the command line.")

    input_file = arguments[0]
    
    if options.output_file == "-":
        output_file = sys.stdout
    else:
        output_file = open(options.output_file, "w")

    verbose = options.verbose

    thumbs_per_page = int(options.thumbs_per_page)

    margin_width = parse_length(options.margin_width)
    thumb_spacing = parse_length(options.thumb_spacing)

    paper_size_name = options.output_paper_size
    paper_size = parse_paper_size(paper_size_name, False)
    paper_width, paper_height = paper_size

    input_paper_size_name = options.input_paper_size
    input_paper_size = parse_paper_size(input_paper_size_name, False)
    input_paper_width, input_paper_height = input_paper_size
    
    available_space = paper_height \
                      - (2*margin_width) \
                      - (thumbs_per_page-1)*thumb_spacing
    
    thumb_height = available_space / float(thumbs_per_page)
    thumb_width = thumb_height * ( input_paper_width / input_paper_height )

    rotate = options.rotate

    ########################################################################
    # Read the source document
    if verbose: print >> sys.stderr, "Reading", input_file
    input_file = open(input_file, "rb")
    input_document = dsc_document.from_file(input_file)
    
    
    ########################################################################
    # Create the output document
    if verbose: print >> sys.stderr, "Creating the output document..."
    output_document = dsc_document()
    od = output_document # Shorthand
    
    od.add_resource(procsets.dsc_eps)
    
    # Document meta data
    od.header.creator = os.environ.get("USER", "")
    od.header.creation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    od.header.document_data = "Binary" # safe for all input documents
    od.header.for_ = os.environ.get("USER", "")
    od.header.language_level = input_document.header.language_level
    od.header.orientation = "Portrait"
    od.header.page_order = "Ascend" 

    thumb_boxes = thumb_box_factory(**locals())

    print >> od.prolog, "/my_showpage { showpage } bind def"

    # This prolog (c) by Angus J. C. Duggan from the psutils package.
    print >> od.prolog, """\
    userdict begin
   [/showpage/erasepage/copypage]{dup where{pop dup load
    type/operatortype eq{1 array cvx dup 0 3 index cvx put
    bind def}{pop}ifelse}{pop}ifelse}forall
   [/letter/legal/executivepage/a4/a4small/b5/com10envelope
    /monarchenvelope/c5envelope/dlenvelope/lettersmall/note
    /folio/quarto/a5]{dup where{dup wcheck{exch{}put}
    {pop{}def}ifelse}{pop}ifelse}forall
   /setpagedevice {pop}bind 1 index where{dup wcheck{3 1 roll put}
    {pop def}ifelse}{def}ifelse
   /PStoPSmatrix matrix currentmatrix def
   /PStoPSxform matrix def/PStoPSclip{clippath}def
   /defaultmatrix{PStoPSmatrix exch PStoPSxform exch concatmatrix}bind def
   /initmatrix{matrix defaultmatrix setmatrix}bind def
   /initclip[{matrix currentmatrix PStoPSmatrix setmatrix
    [{currentpoint}stopped{$error/newerror false put{newpath}}
    {/newpath cvx 3 1 roll/moveto cvx 4 array astore cvx}ifelse]
    {[/newpath cvx{/moveto cvx}{/lineto cvx}
    {/curveto cvx}{/closepath cvx}pathforall]cvx exch pop}
    stopped{$error/errorname get/invalidaccess eq{cleartomark
    $error/newerror false put cvx exec}{stop}ifelse}if}bind aload pop
    /initclip dup load dup type dup/operatortype eq{pop exch pop}
    {dup/arraytype eq exch/packedarraytype eq or
     {dup xcheck{exch pop aload pop}{pop cvx}ifelse}
     {pop cvx}ifelse}ifelse
    {newpath PStoPSclip clip newpath exec setmatrix} bind aload pop]cvx def
   /initgraphics{initmatrix newpath initclip 1 setlinewidth
    0 setlinecap 0 setlinejoin []0 setdash 0 setgray
    10 setmiterlimit}bind def
   end"""

    print >> od.prolog, "/showpage {  } bind def"
    
    # DocumentNeededResources
    needed_resources = dsc_resource_set()
    dr = input_document.header.document_needed_resources
    if dr is not None and len(dr) > 0:
        for r in rd:
            needed_resources.add(r)

    for font_name in input_document.header.document_needed_fonts:
        needed_resources.append(resource_identifyer("font", font_name))
    # I'm not doing this for procsets, because my files here don't use
    # DocumentNeededProcset at all and I would have to parse version info.
    
    # SuppliedResources (these are calculated, actually)
    # The resources are copied at a later point in time, after the Header has
    # been written.
    supplied_resources = dsc_resource_set()
    for resource in input_document.resources():
        od.prolog.append(resource.section)

    for font_name in input_document.header.document_supplied_fonts:
        supplied_resources.append(resource_identifyer("font", font_name))

    # Copy the resources
    for resource in supplied_resources:
        print >> od.prolog, "\n%" + "*" * 50
        print >> od.prolog, "\n%" + "*" * 50

    # Create a setup section.
    # The setup sections are copied as they are. This may implied that
    # resources contained in the setup sections are duplicated.
    if input_document.has_subsection("setup"):
        setup_section = input_document.setup
        fp = setup_section.subfile
        fp.seek(0)
        lines = line_iterator(fp)
        lines.next() # skip first line: %% BeginSetup
        for line in lines:
            if not line.startswith("%%EndSetup"):
                od.setup.write(line)
            
        print >> od.setup

    # Copy (and scale) the pages
    for counter, input_page in enumerate(input_document.pages):
        thumb_box = thumb_boxes.next()

        # Scale factor
        scale_w = thumb_box.w() / input_paper_width
        scale_h = thumb_box.h() / input_paper_height

        scale = min(scale_w, scale_h)

        print >> thumb_box, "psg_begin_epsf"

        if rotate: print >> thumb_box, "0 %f translate" % thumb_height
        print >> thumb_box, "%f %f scale" % ( scale, scale, )
        if rotate: print >> thumb_box, "-90 rotate"
            
        
        # Seek forward to the %%EndPageComments comment or, if none is found,
        # just skip the %%Page comment.
        input_page.subfile.seek(0)
        lines = line_iterator(input_page.subfile)
        for line in lines:
            if line.startswith("%%EndPageComments"):
                break

        if input_page.subfile.tell() == input_page.subfile.length:
            # This means there is no %%EndPageComments line.
            # OpenOffice does this.
            input_page.subfile.seek(0)
            lines = line_iterator(input_page.subfile)
            lines.next() # Skip %%Page line.

        if verbose: print >> sys.stderr, "Copying page", counter + 1
        copy_linewise(input_page.subfile, thumb_box, ignore_comments=True)
        print >> thumb_box
        print >> thumb_box, "psg_end_epsf"

        

    for page in output_document.pages:
        print >> page, "my_showpage"
        
    output_document.write_to(output_file)



main(sys.argv, __doc__)

