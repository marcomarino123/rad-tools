import sys
from os.path import abspath

from rad_tools import __version__

sys.path.insert(0, abspath(".."))


# Project information
project = "rad-tools"
copyright = "2022, Andrey Rybakov"
author = "Andrey Rybakov"

# Project version
version = __version__


# -- General configuration
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.extlinks",
    "numpydoc",
    "sphinx_copybutton",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.mathjax",
    "sphinx_design",
    "sphinx.ext.doctest",
]

autosummary_generate = True
autodoc_member_order = "alphabetical"

smartquotes = False

# Extlinks
extlinks = {
    "examples": (
        "https://github.com/adrybakov/rad-tools/tree/stable/docs/examples/%s",
        "%s",
    ),
    "DOI": ("https://doi.org/%s", "DOI: %s"),
    "numpy": (
        "https://numpy.org/doc/stable/reference/generated/numpy.%s.html",
        "numpy.%s",
    ),
}

# todo
todo_include_todos = True

# Solve the problem with warnings
numpydoc_class_members_toctree = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# exclude console promt sign $ from being copied
copybutton_exclude = ".go"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "pydata_sphinx_theme"
# html_theme = 'alabaster'
# html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["rad-tools.css"]

# Logo
# html_logo = 'img/logo-black.png'
html_title = f"{project} {version}"
html_favicon = "img/favicon.png"

if ".dev" in version:
    switcher_version = "dev"
else:
    major, minor, rest = version.split(".")[0:3]
    switcher_version = f"{major}.{minor}"
html_theme_options = {
    "github_url": "https://github.com/adrybakov/rad-tools",
    "twitter_url": "https://twitter.com/adrybakov",
    "collapse_navigation": True,
    "use_edit_page_button": True,
    "navbar_end": ["theme-switcher.html", "version-switcher", "navbar-icon-links.html"],
    "switcher": {
        "version_match": switcher_version,
        "json_url": "https://rad-tools.adrybakov.com/en/stable/_static/versions.json",
    },
    "navbar_align": "content",
    "logo": {
        "image_light": "_static/logo_black.png",
        "image_dark": "_static/logo_white.png",
    },
    "icon_links": [],  # pydata bugfix
}

# fix problem with autosummary and numpydoc:
numpydoc_show_class_members = False


# html_sidebars = {"**": ["search-field.html", "sidebar-nav-bs", "sidebar-ethical-ads"]}

htmlhelp_basename = "rad-tools"

html_context = {
    "default_mode": "light",
    "display_github": True,  # Integrate GitHub
    "github_user": "adrybakov",  # Username
    "github_repo": "rad-tools",  # Repo name
    "github_version": "master",  # Version
    "doc_path": "docs/source",  # Path in the checkout to the docs root
    # "docsearch_disabled": False,
}


# Custom variables with access from .rst files and docstrings

variables_to_export = [
    "project",
    "copyright",
    "version",
]

frozen_locals = dict(locals())
rst_epilog = "\n".join(
    map(lambda x: f".. |{x}| replace:: {frozen_locals[x]}", variables_to_export)
)
del frozen_locals

# Custom substitutions for links. Solution source:
# https://docutils.sourceforge.io/docs/ref/rst/directives.html#directives-for-substitution-definitions
custom_links = {
    "ANSI": ("ANSI", "https://en.wikipedia.org/wiki/ANSI_escape_code"),
    "projwfc": ("projwfc.x", "https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.html"),
    "QE": ("Quantum Espresso", "https://www.quantum-espresso.org"),
    "TB2J": ("TB2J", "https://tb2j.readthedocs.io/en/latest/"),
    "Wannier90": ("Wannier90", "http://www.wannier.org/"),
    "Python": ("Python", "https://python.org"),
    "NumPy": ("NumPy", "https://numpy.org/"),
    "SciPy": ("SciPy", "https://scipy.org/"),
    "matplotlib": ("matplotlib", "https://matplotlib.org/"),
    "tqdm": ("tqdm", "https://tqdm.github.io/"),
    "termcolor": ("termcolor", "https://pypi.org/project/termcolor/"),
    "Python-installation": (
        "Python installation",
        "https://wiki.python.org/moin/BeginnersGuide/Download",
    ),
    "pytest": ("pytest", "https://docs.pytest.org/en/7.3.x/"),
    "latex": ("LaTeX", "https://www.latex-project.org/"),
    "black": ("black", "https://black.readthedocs.io"),
    "array_like": (
        "array_like",
        "https://numpy.org/doc/stable/glossary.html#term-array_like",
    ),
    "termcolor": ("termcolor", "https://github.com/termcolor/termcolor"),
    "PearsonSymbol": ("Pearson symbol", "https://en.wikipedia.org/wiki/Pearson_symbol"),
    "matplotlibFocalLength": (
        "3D plot projection types",
        "https://matplotlib.org/stable/gallery/mplot3d/projections.html",
    ),
    "matplotlibSavefig": (
        "plt.savefig()",
        "https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html",
    ),
    "matplotlibViewInit": (
        "view_init",
        "https://matplotlib.org/stable/api/_as_gen/mpl_toolkits.mplot3d.axes3d.Axes3D.view_init.html",
    ),
    "matplotlibLegend": (
        "legend()",
        "https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.legend.html",
    ),
    "matplotlibColor": (
        "matplotlib colors",
        "https://matplotlib.org/stable/tutorials/colors/colors.html",
    ),
}


rst_epilog += "\n".join(
    map(
        lambda x: f"\n.. |{x}| replace:: {custom_links[x][0]}\n.. _{x}: {custom_links[x][1]}",
        [i for i in custom_links],
    )
)
