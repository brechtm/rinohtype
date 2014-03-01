# -*- coding: utf-8 -*-

import time

before_time = time.clock()
from rfic2009style import RFIC2009Paper
# from citeproc.source.bibtex import BibTeX
after_time = time.clock()
import_time = after_time - before_time
print('Module import time: {:.2f} seconds'.format(import_time))

before_time = time.clock()
# bib_source = BibTeX('references.bib')
# doc = RFIC2009Paper('template.xml', bib_source)
doc = RFIC2009Paper('template.xml', None)
after_time = time.clock()
setup_time = after_time - before_time
print('Setup time: {:.2f} seconds'.format(setup_time))

before_time = time.clock()
doc.render('template')
after_time = time.clock()
render_time = after_time - before_time
print('Render time: {:.2f} seconds ({:.2f}s per page)'
      .format(render_time, render_time / doc.page_count))

total_time = import_time + setup_time + render_time
print('Total time: {:.2f} seconds'.format(total_time))
