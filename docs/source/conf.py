"""Sphinx configuration for News 4 U's API and application reference."""

import os
import sys
from pathlib import Path

import django

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

project = "News 4 U"
copyright = "2026, News 4 U contributors"
author = "News 4 U contributors"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = ["_build", "generated", ".doctrees"]

html_theme = "alabaster"
