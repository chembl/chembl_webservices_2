#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'mnowotka'

import sys

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

if sys.version_info < (2, 7, 3) or sys.version_info >= (3, 0, 0):
    raise Exception('ChEMBL software stack requires python 2.7.3 - 3.0.0')

setup(
    name='chembl-webservices',
    version='2.7.7',
    author='Michal Nowotka',
    author_email='mnowotka@ebi.ac.uk',
    description='Python package providing chembl web services API.',
    url='https://www.ebi.ac.uk/chembldb/index.php/ws',
    license='Apache Software License',
    packages=[
        'chembl_webservices',
        'chembl_webservices.core',
        'chembl_webservices.resources',
        'chembl_webservices.management',
        'chembl_webservices.management.commands',
    ],
    long_description=open('README.md').read(),
    install_requires=[
        'lxml',
        'PyYAML>=3.10',
        'defusedxml>=0.4.1',
        'simplejson==2.3.2',
        'Pillow>=2.1.0',
        'django-tastypie==0.13.3',
        'chembl-core-model>=0.9.29',
        'cairocffi>=0.5.1',
        'numpy>=1.7.1',
        'mimeparse',
        'raven>=3.5.0',
        'chembl_beaker>=1.1.12',
        'pysolr==2.1.0',
        'django-haystack==2.6.0',
    ],
    include_package_data=True,
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Scientific/Engineering :: Chemistry'],
    zip_safe=False,
)
