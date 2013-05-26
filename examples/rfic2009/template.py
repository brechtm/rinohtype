# -*- coding: utf-8 -*-

import os
import time

time.clock()

from rfic2009style import RFIC2009Paper
from citeproc.source.bibtex import BibTeX


bib_source = BibTeX('references.bib')

doc = RFIC2009Paper('template.xml', bib_source)

setup_time = time.clock()
print('Setup time: {:.2f} seconds'.format(setup_time)) # parsing XML and fonts

doc.render('template')

run_time = time.clock()
render_time = run_time - setup_time
print('Render time: {:.2f} seconds ({:.2f}s per page)'
      .format(render_time, render_time / doc.page_count))
print('Total execution time: {:.2f} seconds'.format(run_time))

#os.system("ps2pdf.cmd")
