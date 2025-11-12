# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "python-template"
copyright = "2025, yu9824"
author = "yu9824"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # docstringからドキュメントを作成してくれる。
    "sphinx.ext.napoleon",  # google式・numpy式docstringを整形してくれる。
    "sphinx.ext.githubpages",  # github-pages用のファイルを生成してくれる。
    "myst_nb",
    "sphinx_book_theme",
    "jupyter_sphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]

# テーマのオプション設定
html_theme_options = {
    "show_toc_level": 2,  # TOCの表示レベル（見出しの深さ、1-3の範囲）
}

# MyST-NB（ノートブック統合）の設定
nb_execution_mode = "off"  # 実行を無効に（後でonにしてもよい）

# MyST の拡張（$$で数式など）
myst_enable_extensions = [
    "dollarmath",
    "colon_fence",
]
