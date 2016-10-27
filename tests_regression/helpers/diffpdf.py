import os
import subprocess


DIFFPDF_SH = os.path.join(os.path.dirname(__file__), 'diffpdf.sh')


def diff_pdf(a_filename, b_filename):
    rc = subprocess.call(['bash', DIFFPDF_SH, a_filename, b_filename])
    return rc == 0
