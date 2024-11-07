# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import django

# Add the project path to the sys.path
sys.path.insert(0, os.path.abspath('../'))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'Project.settings'  # Replace 'Project.settings' with your Django settings module

# Initialize Django
django.setup()


project = 'document_assistant'
copyright = '2024, Derrick Kirimi'
author = 'Derrick Kirimi'
release = '1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
