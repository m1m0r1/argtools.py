import os
import sys
from setuptools import setup, find_packages

REQUIRES = ['argparse'] if sys.version_info < (2, 7) else []
README = os.path.join(os.path.dirname(__file__), 'README.md')
long_description = open(README).read() + '\n\n'
VERSION = '0.1.0'

setup(name='argtools',
      version=VERSION,
      install_requires=REQUIRES,
      description='A wrapper of argparse that helps to build command line tools with minimal effort.',
      long_description=long_description,
      classifiers=['Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules'],
      keywords='argparse subcommand command cli',
      author='Takahiro Mimori',
      author_email='takahiro.mimori@gmail.com',
      url='https://github.com/m1m0r1/argtools.py',
      )
