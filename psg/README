PostScript Generator (psg)
==========================

Psg is a Python module to create PostScript documents which adhere to
Adobe's Document Structuring Conventions from scratch or read them
from complient PostScript files.

- It lets you create PostScript files by embedding EPS files, bitmaps,
  fonts and arbitrary subsections from DSC complient input files. This
  could be used to re-write the psutils package in Python.

- I do not intend to implement drawing primitives, there are already
  libraries that do that very well. However, I plan to create an
  interface between psg and pyscript, a PostScript creation module which
  focuses on drawing end geometry.

- Text is a different subject, though. A rudimentary layout engine to
  create connected text boxes is in place and will be extended in the
  future. I envision a subset of XML/CSS. The text functons support
  Type1 fonts and dynamically re-encodes them based on unicode(!) input.

- All input/output operation goes through regular Python file
  objects. (This may seem an odd thing to mention as a 'feature'. But
  trust me, it's special).

- Though PostScript files are generally constructed in memory, all
  import operations are 'lazy', that is, input files are analyzed but
  their content is only copied over to the outfile in the last step of
  composition to reduce memory footprint.

- Psg contains classes to model a PostScript run time environment
  (namely Ghostscript). It will contain functionality to use Ghostscript
  to create PDF files and bitmap previews (my own use is largely www
  applications), but also to import PDF and those PostScript files that
  make use of all the DSC's liberties.

- There is no coherent documentation, yet, but the source code is
  richly and (I hope) usefully documented.

Check out the examples/ directory. Besides a number of scripts it also
contains the Number Serif font from GNU Ghostscript so you can start
creating PostScript documents right away! The conditions*.py files
contain a real world example I wrote using psg and that is in
production use.

Every kind of feedback is strongly encouraged!

Diedrich Vorberg <diedrich@tux4web.de> 



--

$Log: README,v $
Revision 1.2  2006/10/16 12:52:43  diedrich
Changed my CVS Root to Savannah, commiting changes since the upload.

Revision 1.2  2006/10/15 17:34:35  t4w00-diedrich
Added remark on examples/.

Revision 1.1  2006/09/06 23:22:50  t4w00-diedrich
Initial commit
