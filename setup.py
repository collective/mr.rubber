from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='mr.rubber',
      version=version,
      description="Supervisor plugin that ensures one process per cpu",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='supervisord',
      author='Dylan Jay',
      author_email='software@pretaweb.com',
      url='',
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
