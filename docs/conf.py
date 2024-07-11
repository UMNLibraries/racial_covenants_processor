import os
import sys
import django

from datetime import date

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../src"))
# os.environ['DJANGO_SETTINGS_MODULE'] = 'racial_covenants_processor.settings'
os.environ["DJANGO_SETTINGS_MODULE"] = "docs.django_settings"
django.setup()


# Configure the path to the Django settings module
django_settings = "docs.django_settings"

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'The Deed Machine'
copyright = f'{date.today().year} Regents of the University of Minnesota'
author = 'Mapping Prejudice'
release = '1.0 dev1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinxcontrib_django']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
