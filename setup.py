#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.rst') as history_file:
    history = history_file.read()

requirements = [
    'kinto>=10.0.0'
]

test_requirements = [
    'mock',
    'unittest2',
    'webtest',
]

setup(
    name='kinto-changes',
    version='1.2.1',
    description="Plug Kinto notifications to a collection endpoint.",
    long_description=readme + '\n\n' + history,
    author='Mozilla Services',
    author_email='services-dev@mozilla.com',
    url='https://github.com/kinto/kinto-changes',
    packages=[
        'kinto_changes',
    ],
    package_dir={'kinto_changes': 'kinto_changes'},
    include_package_data=True,
    install_requires=requirements,
    license="Apache License (2.0)",
    zip_safe=False,
    keywords='kinto changes notification',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
