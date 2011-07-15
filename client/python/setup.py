#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
 
setup(
    name='sin-python-client',
    version='0.1-SNAPSHOT',
    description='This library implements a Sin client',
    url='https://github.com/wonlay/sin',
    packages=['sinClient'],
    package_dir={'sinClient': 'src/sinClient'},
    package_data={'sinClient': ['data/test.json']},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Service",
        "License :: Apache Public License v.2.0",
    ],
)
