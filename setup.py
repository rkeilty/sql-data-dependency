#!/usr/bin/env python
from setuptools import setup, find_packages

install_requires = [
    'MySQL-python>=1.0.0',
    'SQLAlchemy>=1.0.0',
]

f = open('README.rst')
readme = f.read()
f.close()

setup(
    name='sqldd',
    version='0.9.2',
    author='Rick Keilty',
    author_email='rkeilty@gmail.com',
    url='http://github.com/rkeilty/sql-data-dependency',
    description='A toolkit for analyzing dependencies in SQL databases.',
    long_description=readme,
    license='BSD',
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    scripts=[
        'bin/sqldd'
    ],
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development'
    ],
)
