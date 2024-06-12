# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

import sys
import os
sys.path.insert(0, 'src')

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if not os.path.exists('README.rst'):
    import pypandoc
    pypandoc.download_pandoc(targetfolder='~/bin/')
    pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mas-cli',
    version='1.0.0',
    author='David Parker',
    author_email='parkerda@uk.ibm.com',
    package_dir={'': 'src'},
    packages=[
        'mas.cli',
        'mas.devops',
    ],
    namespace_packages=['mas'],
    url='https://github.com/ibm-mas/cli',
    license='Eclipse Public License - v1.0',
    description='Python SDK for Maximo Application Suite',
    long_description=long_description,
    install_requires=[
        'halo',           # MIT License
        'prompt_toolkit', # BSD License
        'pyyaml',         # MIT License
        'openshift',      # Apache Software License
        'kubernetes',     # Apache Software License
        'kubeconfig',     # BSD License
        'jinja2'          # BSD License
    ],
    extras_require={
        'dev': [
            'build',       # MIT License
            'pytest',      # MIT License
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
