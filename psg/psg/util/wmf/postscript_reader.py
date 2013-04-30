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
# $Log: postscript_reader.py,v $
# Revision 1.2  2006/12/10 22:52:28  diedrich
# Did some more work on the PostScript reader, testing.
#
# Revision 1.1  2006/12/10 01:10:59  diedrich
# Initial commit
#
#


import sys, struct
from string import *

from reader import wmf_reader
from wmfutil import *

from psg.document.dsc import eps_document
from psg.debug import debug

def pscolor_operator(color):
    #if color[0] == color[1] == color[2]:
    #    return "%i setgray" % ( float(color[0]) / 100.0 )
    #else:
    color = map(lambda v: float(v) / 100.0, color)
    return "%.2f %.2f %.2f setrgbcolor" % tuple(color)

def points_from_list(values):
    i = values.__iter__()

    try:
        while True:
            x = i.next()
            y = i.next()
            yield ( x, y, )
        
    except StopIteration:
        pass

class postscript_reader(wmf_reader):
    class _output(wmf_reader._output):
        def __init__(self, reader, fp):
            wmf_reader._output.__init__(self, reader, fp)
            self._select_object_counter = 0

            self._windoworg = None
            self._viewportorg = None
            self._windowext = None
            self._viewportext = None

            self._gsaved = False
            self._gset = False

            print >> debug, "#" * 78

            # Scale and translate the PostScript GC to match the wmf's
            # bounding box and GUI like geometry.

            #if debug.verbose:
            #    print >> self, "144 288 translate"
            #    print >> self, "0.5 0.5 scale"
            
            bb = self.reader.bounding_box
            scale = 72.0 / float(self.reader.resolution)
            print >> self, scale, -scale, "scale"          # turn y axis

            # In debug mode, draw a bounding box (in wmf coordinates)
            if debug.verbose:
                print >> self, "gsave % bounding box begin"
                # Set drawing context to wmf coords
                print >> self, "%i %i translate" % (-bb.left, -bb.bottom) 
                print >> self, "newpath",
                print >> self, "%f %f moveto" % ( bb.left, bb.top, ),
                print >> self, "%f %f lineto" % ( bb.right, bb.top, )
                print >> self, "%f %f lineto" % ( bb.right, bb.bottom, ),
                print >> self, "%f %f lineto" % ( bb.left, bb.bottom, )
                print >> self, "closepath",
                print >> self, "1 0 0  setrgbcolor",
                print >> self, "2 setlinewidth",
                print >> self, "[5 5] 0 setdash",
                print >> self, "stroke"
                print >> self, "grestore % bounding box end"
            
        def finish(self):
            """
            Overload _output.finish() to prevent close() to be called
            on fp, because fp may or may not be a regular file.
            """
            pass

        def write(self, s):
            """
            Provide a write() function to make::

               print >>

            work correctly. This is usefull for PostScript programming.
            """
            if self._gset: self.gset()
            self.fp.write(s)

        def new_select_object_no(self):
            self._select_object_counter += 1
            return self._select_object_counter

        def setwindoworg(self, x, y):
            self._windoworg = ( x, y, )
            self._viewportorg = None
            self._gset = True

        def setwindowext(self, w, h):
            self._windowext = ( w, h, )
            self._gset = True

        def setviewportorg(self, x, y):
            self._viewportorg = ( x, y, )
            self._windoworg = None
            self._gset = True

        def setviewportext(self, w, h):
            self._viewportorg = ( w, h, )
            self._gset = True

        def gset(self):
            """
            Restore Postscripts Graphics Context to the state we've
            started out with and set scaling and translation to
            appropriate values.
            """
            if self._gsaved: print >> self.fp, "grestore"
            print >> self.fp, "gsave"
            self._gsaved = True
            
            mapmode = self.reader.current_dc.mapmode

            if self._viewportorg is not None:
                print >> self.fp, "%f %f translate" % self._viewportorg

            if mapmode == "isotropic" or mapmode == "anisotropic":
                bb = ( self.reader.bounding_box.width(),
                       self.reader.bounding_box.height(), )
                
                if self._windowext is None:
                    windowext = bb
                else:
                    windowext = self._windowext

                scale_x = float(bb[0]) / float(windowext[0]) 
                scale_y = float(bb[1]) / float(windowext[1])
                
                if self._viewportext is not None:
                    raise "FIXME!"
                    
                print "exts",  "bb", bb, "winext", windowext,
                print "scale", (scale_x, scale_y,)
                
                
            if self._windoworg is not None: 
                bb = self.reader.bounding_box

                if debug.verbose:
                    print >> self.fp, \
                                "gsave 0 1 0 setrgbcolor % coord cross begin"
                    print >> self.fp, \
                                "newpath 0 1000 moveto 0 -1000 lineto stroke"
                    print >> self.fp, \
                                "newpath 1000 0 moveto -1000 0 lineto stroke"
                    print >> self.fp, \
                                "grestore                % coord cross end"
                    
                x = abs(self._windoworg[0])
                y = -(bb.height() - abs(self._windoworg[1]))
                print >> self.fp, "%f %f translate" % ( x, y, ), "% windoworg"

                if self._windowext[1] < 0:
                    print >> self.fp, "1 -1 scale"

                if debug.verbose:
                    print >> self.fp, \
                          "gsave 0 1 0 setrgbcolor % coord cross begin"
                    print >> self.fp, \
                          "newpath 0 1000 moveto 0 -1000 lineto stroke"
                    print >> self.fp, \
                          "newpath 1000 0 moveto -1000 0 lineto stroke"
                    print >> self.fp, \
                          "grestore                % coord cross end"

                
            if mapmode == "text":
                pass
            elif mapmode == "loenglish": # 1/100"
                print >> self.fp, "0.72 0.72 scale"
            elif mapmode == "hienglish": # 1/1000"
                print >> self.fp, "0.072 0.072 scale"
            elif mapmode == "lometric": # 1/10mm
                print >> self.fp, "0.283 0.283 scale"
            elif mapmode == "himetric": # 1/10mm
                print >> self.fp, "0.0283 0.0283 scale"
            elif mapmode == "twips": # 1/20pt
                print >> self.fp, "0.05 0.05 scale"
            elif mapmode == "isotropic":
                scale = min(scale_x, scale_y)
                if scale != 1.0:
                    print >> self.fp, scale, scale, "scale % isotropic"
            elif mapmode == "anisotropic":
                pass
                if scale_x != 1.0 and scale_y != 1.0:
                    print >> self.fp, scale_x, scale_y, "scale % anisotropic"


            self._gset = False
            
        def finish(self):
            print >> self.fp, "grestore"
            

    # Drawing Tools
    # oo -> output_object

    # The postscript_reader's select_objects all have a use() method,
    # which will output PostScript suitable to set the drawing tool and
    # call the appropriate PostScrupt operator to apply it to the current
    # path.

    class _pen(wmf_reader._pen):
        ps_styles = { "solid": "[] 0",
                      "dash": "[3 3] 0",
                      "dot": "[1 1] 0", 
                      "dashdot": "[3 1 1 1] 0",
                      "dashdotdot": "[3 1 1 1 1 1] 0",
                      "null": None,
                      "insideframe": None,
                      "userstyle": None,  
                      "alternate": None, }

        ps_joins = { "round": 1,
                     "bevel": 2,
                     "miter": 0,
                     "mask": 0, }

        def create(self, oo):
            self.ps_name = "pen$%i" % oo.new_select_object_no()
            
            print >> oo, "/" + self.ps_name, "{",
            # Style
            ps_style = self.ps_styles[self.style]
            if ps_style is not None:
                print >> oo, ps_style, "setdash",

            # Width
            print >> oo, self.width[0], "setlinewidth",

            # Color
            print >> oo, pscolor_operator(self.color),

            # Endcaps
            if self.endcaps == "round":
                linecap = 1
            else:
                linecap = 0

            print >> oo, linecap, "setlinecap",

            # Joins
            print >> oo, self.ps_joins[self.join], "setlinejoin",

            print >> oo, "} def"

        def use(self, oo):
            if self.style != "null":
                print >> oo, self.ps_name, "stroke"


    class _brush(wmf_reader._brush):
        def create(self, oo):
            self.ps_name = "brush$%i" % oo.new_select_object_no()

            print >> oo, "/" + self.ps_name, "{",
            print >> oo, pscolor_operator(self.color),
            print >> oo, "} def"

        def use(self, oo):
            if self.style != "null":
                print >> oo, self.ps_name, "fill"
            

    # Function classes (normal param mechanism)
    class setwindoworg(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            oo.setwindoworg(x, y)            

    class offsetwindoworg(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            oo.setwindoworg(self.reader._windoworg[0] + x,
                            self.reader._windoworg[1] + y)
            
    class setwindowext(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            oo.setwindowext(x, y)


    class setviewportorg(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            oo.setviewportorg(x, y)            

    class offsetviewportorg(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            oo.setviewportorg(self.reader._viewportorg[0] + x,
                            self.reader._viewportorg[1] + y)
            
    class scaleviewportorg(wmf_reader._normal_function):
        def draw(self, oo, yDenom, yNum, xDenom, xNum):
            oo.setviewportorg((self.reader._viewportorg[0] * xNum) / xDenom,
                              (self.reader._viewportorg[1] * yNum) / yDenom)
                              
            
    class setviewportext(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            oo.setviewportext(x, y)


    class modeto(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            print >> oo, x, y, "moveto"

    class linetoto(wmf_reader._normal_function):
        def draw(self, oo, y, x):
            print >> oo, x, y, "lineto"
            self.reader.current_dc.pen.use(oo)

    class rectangle(wmf_reader._normal_function):
        def draw(self, oo, bottom, right, top, left):
            print >> oo, "newpath",
            print >> oo, "%f %f moveto" % ( left, top, ),
            print >> oo, "%f %f lineto" % ( right, top, )
            print >> oo, "%f %f lineto" % ( right, bottom, ),
            print >> oo, "%f %f lineto" % ( left, bottom, )
            print >> oo, "closepath"
            
            self.reader.current_dc.brush.use(oo)
            self.reader.current_dc.pen.use(oo)
            
            
            
    class ellipse(wmf_reader._normal_function):
        def draw(self, oo, bottom, right, top, left):
            print >> oo, "gsave"
            print >> oo, "newpath"
            print >> oo, "/savematrix matrix currentmatrix def"
            print >> oo, left + (abs(right-left) / 2),
            print >> oo, top  + (abs(bottom-top) / 2), "translate"
            
            print >> oo, abs(right-left) / 2, abs(bottom-top) / 2 , "scale"
            print >> oo, "0 0 1 0 360 arc"
            print >> oo, "savematrix setmatrix"
            
            self.reader.current_dc.brush.use(oo)
            self.reader.current_dc.pen.use(oo)

            print >> oo, "grestore"
            
            

    # Function classes (custom param mechanism)
    class polyline(wmf_reader._meta_function):
        def playback(self, oo):
            tpl = self.reader.stream.read_fmt("<H")
            number_of_points = tpl[0]
            vals = self.reader.stream.read_fmt("<%ih" % (number_of_points*2))
            points = points_from_list(vals)
            
            print >> oo, "newpath"

            first = True
            for point in points:
                if first:
                    print >> oo, point[0], point[1], "moveto" 
                    first = False
                else:
                    print >> oo, point[0], point[1], "lineto" 

            self.reader.current_dc.pen.use(oo)

    class polygon(polyline):
        def playback(self, oo):
            tpl = self.reader.stream.read_fmt("<H")
            number_of_points = tpl[0]
            vals = self.reader.stream.read_fmt("<%ih" % (number_of_points*2))
            points = points_from_list(vals)
            
            print >> oo, "newpath"

            first = True
            for point in points:
                if first:
                    print >> oo, point[0], point[1], "moveto" 
                    first = False
                else:
                    print >> oo, point[0], point[1], "lineto" 
            
            print >> oo, "closepath"
            self.reader.current_dc.brush.use(oo)
            self.reader.current_dc.pen.use(oo)
            

    class polypolygon(wmf_reader._meta_function):
        def playback(self, oo):
            tpl = self.reader.stream.read_fmt("<H")
            number_of_polygons = tpl[0]
            polygon_sizes = self.reader.stream.read_fmt(
                "<%ih" % (number_of_polygons))

            for number_of_points in polygon_sizes:
                vals = self.reader.stream.read_fmt(
                    "<%ih" % (number_of_points*2))
                points = points_from_list(vals)

                print >> oo, "newpath"

                first = True
                for point in points:
                    if first:
                        print >> oo, "%f %f moveto" % point
                        first = False
                    else:
                        print >> oo, "%f %f lineto" % point

                print >> oo, "closepath"
                self.reader.current_dc.pen.use(oo)
                self.reader.current_dc.brush.use(oo)


                
class color_ps:
    """
    This colorizes output ps. Used for debugging.
    """
    def __init__(self, fp):
        self.fp = fp
        
    def write(self, s):
        sys.stdout.write("\033[1;34m")
        if s == "\n":
            sys.stdout.write("\033[0;0m\n")        
        else:
            sys.stdout.write(s)

        if self.fp is not None: self.fp.write(s)
            
def wmf2eps(wmf_fp, title=None):
    """
    Return a psg.document.dsc.eps_document instance containing a rendition
    of the wmf file pointed fo by 'wmf_fp'.

    @param wmf_fp: File pointer open for reading (seeking is not needed)
    @param title: Title string for the EPS document.
    """
    eps = eps_document(title=title)
    page = eps.page
    
    reader = postscript_reader(wmf_fp)

    # This renders the wmf file in memory. If one wanted to comply
    # with psg's 'lazy' pollicy for wmf files, one could easily do so
    # by writing a special subclass of eps_document that keeps a
    # reference to the reader and then calls save() on write_to().

    outstream = eps.page

    # Colorize the PostScript to be able to tell it apart from
    # debugging info.
    if debug.verbose:
        outstream = color_ps(outstream)

    reader.save(outstream)

    width = float(reader.bounding_box.width()) / float(reader.resolution) *72.0
    height = float(reader.bounding_box.height())/float(reader.resolution) *72.0
    eps.header.bounding_box = ( 0, 0, width, height, )
    eps.header.hires_bounding_box = ( 0, 0, width, height, )

    return eps
    
    
    
    
# Local variables:
# mode: python
# ispell-local-dictionary: "english"
# End:

