#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
 
setup(
    name='sin-python-client',
    version='0.1-SNAPSHOT',
    description='This library implements a Sin client',
    url='https://github.com/wonlay/sin',
    packages=['sin'],
    package_dir={'sin': 'src/sin'},
    package_data={'sin': ['data/test.json']},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Service",
        "License :: Apache Public License v.2.0",
    ],
)
