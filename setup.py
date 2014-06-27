from setuptools import setup, find_packages
import sys, os

# Hack to prevent TypeError: 'NoneType' object is not callable error
# on exit of python setup.py test
try:
    import multiprocessing
except ImportError:
    pass

version = '0.3.6.2'

setup(name='xmltool',
      version=version,
      description="Tool to manipulate XML files",
      long_description=open('README.rst').read().split('Build Status')[0],
      classifiers=[
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: JavaScript',
        'Topic :: Text Processing :: Markup :: XML',
        'Topic :: Text Processing :: Markup :: HTML',
      ],
      keywords='',
      author='Aur\xc3\xa9lien Matouillot',
      author_email='a.matouillot@gmail.com',
      url='http://xmltool.lereskp.fr/',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'lxml',
          'WebOb',
          'requests',
      ],
      test_suite='nose.collector',
      tests_require=[
          'nose',
          'BeautifulSoup',
          'strainer',
          'FormEncode',
          'tw2.core',
          'WebTest',
          'sieve>=0.1.9',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
