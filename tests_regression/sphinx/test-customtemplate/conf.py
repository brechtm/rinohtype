# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Custom Template'
copyright = '1999, Author'
author = 'Author'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for rinohtype PDF output ----------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath('.'))

import mytemplate

rinoh_documents = [dict(
    doc='index',
    target='customtemplate',
    template='mytemplate.rtt',
)]
