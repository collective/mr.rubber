from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(name='mr.rubber',
      version=version,
      description="your elastic friend to start supervisord processes based on cpu cores available",
      long_description="""\
"""+open("README.rst").read(),
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='supervisord',
      author='Dylan Jay',
      author_email='software@pretaweb.com',
      url='http://pypi.python.org/pypi/mr.rubber',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "supervisor",
          # -*- Extra requirements: -*-
      ],
      entry_points = {
                      'console_scripts': ['rubber = mrrubber.rubber:main'],
                      },
      )
