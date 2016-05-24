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
    'kinto>=1.10'
]

test_requirements = [
    'mock',
    'unittest2',
    'webtest',
]

setup(
    name='kinto-changes',
    version='0.3.0',
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
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
