from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='django-db-quick-setup',
      description='Create and start MySQL/PostgreSQL containers with a single '
      'management command',
      long_description=long_description,
      keywords='django mysql postgresql docker',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Utilities',
      ],
      license='BSD',
      author='Aleksandr Mezin',
      author_email='mezin.alexander@gmail.com',
      url='https://github.com/amezin/django-db-quick-setup',
      use_scm_version=True,
      setup_requires=['setuptools_scm'],
      install_requires=['Django', 'docker-py'],
      packages=find_packages(include=['db_quick_setup', 'db_quick_setup.*']))
