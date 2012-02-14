# -*- coding: utf-8 -*-

import os
import time

time.clock()

from rfic2009style import RFIC2009Paper
from pyte.bibliography import PseudoCSLDataXML

bib_source = PseudoCSLDataXML('references.xml')

doc = RFIC2009Paper('template.xml', bib_source)
doc.render('template')

run_time = time.clock()

print('Total execution time: {} seconds'.format(run_time))

#os.system("ps2pdf.cmd")
