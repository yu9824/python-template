# python-template

<!-- badges -->
[![CI](https://github.com/yu9824/python-template/actions/workflows/CI.yml/badge.svg)](https://github.com/yu9824/python-template/actions/workflows/CI.yml)
[![docs](https://github.com/yu9824/python-template/actions/workflows/docs.yml/badge.svg)](https://github.com/yu9824/python-template/actions/workflows/docs.yml)
[![release-pypi](https://github.com/yu9824/python-template/actions/workflows/release.yml/badge.svg)](https://github.com/yu9824/python-template/actions/workflows/release.yml)

<!--
[![python_badge](https://img.shields.io/pypi/pyversions/python-template)](https://pypi.org/project/python-template/)
[![license_badge](https://img.shields.io/pypi/l/python-template)](https://pypi.org/project/python-template/)
[![PyPI version](https://badge.fury.io/py/python-template.svg)](https://pypi.org/project/python-template/)
[![Downloads](https://static.pepy.tech/badge/python-template)](https://pepy.tech/project/python-template)

[![Conda Version](https://img.shields.io/conda/vn/conda-forge/python-template.svg)](https://anaconda.org/conda-forge/python-template)
[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/python-template.svg)](https://anaconda.org/conda-forge/python-template)
-->

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://github.com/python/mypy)
<!-- /badges -->

## Using this as a template

Bulk-replace the project name, set up ssh-agent on the host, etc.

## Installation

```bash
# standard
pip install git+https://github.com/yu9824/python-template.git

# with Cython compiling
pip install git+https://github.com/yu9824/python-template.git#subdirectory=packages/setuptools/cython

```

## Directory layout

| Directory | Purpose |
| --- | --- |
| `src/python_template/` | Package source |
| `tests/` | pytest tests |
| `notebooks/` | Notebooks for experimentation (paired with `.py` via jupytext) |
| `data/raw/` | Raw, as-obtained data. Contents are not tracked |
| `data/processed/` | Preprocessed data. Contents are not tracked |
| `models/` | Trained models. Contents are not tracked |
| `docs_src/` | Sphinx source |
| `packages/` | Package templates for different build configurations |
| `examples/` | Example scripts |
