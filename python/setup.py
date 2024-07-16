# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

import codecs
import sys
import os
sys.path.insert(0, 'src')

from setuptools import setup, find_namespace_packages

if not os.path.exists('README.rst'):
    import pypandoc
    pypandoc.download_pandoc(targetfolder='~/bin/')
    pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Maintain a single source of versioning
# https://packaging.python.org/en/latest/guides/single-sourcing-package-version/
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setup(
    name='mas-cli',
    version=get_version("src/mas/cli/__init__.py"),
    author='David Parker',
    author_email='parkerda@uk.ibm.com',
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src'),
    include_package_data=True,
    scripts=[
        'src/mas-cli'
    ],
    url='https://github.com/ibm-mas/cli',
    license='Eclipse Public License - v1.0',
    description='Python Admin CLI for Maximo Application Suite',
    long_description=long_description,
    install_requires=[
        'mas-devops',     # EPL
        'halo',           # MIT License
        'prompt_toolkit', # BSD License
        'openshift',      # Apache Software License
        'kubernetes',     # Apache Software License
        'tabulate'        # MIT License
    ],
    extras_require={
        'dev': [
            'build',       # MIT License
            'flake8',      # MIT License
            'pytest',      # MIT License
            'pyinstaller'  # GPL, https://pyinstaller.org/en/stable/license.html & https://github.com/pyinstaller/pyinstaller/wiki/FAQ#license
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
