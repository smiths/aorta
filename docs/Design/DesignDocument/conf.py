# flake8: noqa

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
project_path = os.path.abspath('../../../')
test_path = os.path.join(project_path, "test")
sys.path.insert(0, test_path)
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)
AGR_lib_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModuleLib")
sys.path.insert(0, AGR_lib_module_path)
sys.path.insert(0, project_path)



# -- Project information -----------------------------------------------------

project = 'AortaGeomRecon'
copyright = '2023, Jingyi Lin'
author = 'Jingyi Lin'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.todo", "sphinx.ext.napoleon"]
# autodoc_mock_imports = ["vtk", "sitkUtils", "PythonQt", "slicer", "ScriptedLoadableModule"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autodoc_default_options = {"members": True, "undoc-members": True, "private-members": True} # noqa

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = [
    '_static/custom.css',
]
