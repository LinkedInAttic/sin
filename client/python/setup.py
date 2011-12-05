#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

try:
  from setuptools import setup, find_packages
except ImportError:
  print 'Error: setuptools is required. http://pypi.python.org/pypi/setuptools'
  sys.exit(1)

setup(
    name               = 'sin-python',
    version            = '0.1',
    description        = 'This library implements a Sin client',
    url                = 'https://github.com/senseidb/sin',
    packages           = find_packages(),
    install_requires   = ['sensei-python>=1.0'],
    dependency_links   = ['https://github.com/downloads/senseidb/sensei/sensei-python-1.0.tar.gz'],
    classifiers        = [
                           "Development Status :: 3 - Alpha",
                           "Topic :: Service",
                           "License :: Apache Public License v.2.0",
                         ],
)
