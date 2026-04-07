"""Sphinx configuration for htcie documentation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

project = "htcie"
copyright = "2024, htcie contributors"
author = "htcie contributors"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

html_theme = "furo"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = True

myst_enable_extensions = ["colon_fence"]

exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]
