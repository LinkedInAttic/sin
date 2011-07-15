#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
 
setup(
    name='sin-python-client',
    version='0.1-SNAPSHOT',
    description='This library implements a Sin client',
    author='LinkedIn.com',
    url='https://github.com/wonlay/sin',
    package_dir={'': 'src'},
    py_modules=[
        'sinClient','kafka','senseiClient'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Service",
        "License :: Apache Public License v.2.0",
    ],
)
