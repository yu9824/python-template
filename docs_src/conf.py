# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from template import __author__, __version__

project = "template"
copyright = "2024, yu9824"
author = __author__
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # docstringからドキュメントを作成してくれる。
    "sphinx.ext.napoleon",  # google式・numpy式docstringを整形してくれる。
    "sphinx.ext.githubpages",  # github-pages用のファイルを生成してくれる。
    "recommonmark",  # markdownで書けるようにする。
    "sphinx_markdown_tables",  # markdownの表を書けるようにする。
    "sphinx_multiversion",  # 複数バージョンの共存
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# markdown
source_suffix = [".rst", ".md"]
source_parsers = {
    ".md": "recommonmark.parser.CommonMarkParser",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]