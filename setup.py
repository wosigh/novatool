#!/usr/bin/env python

from distutils.core import setup

setup(name = 'novatool',
      version = '1.0',
      description = 'A tool for WebOS devices.',
      author = 'Ryan Hope',
      author_email = 'rmh3093@gmail.com',
      url = 'http://http://www.webos-internals.org/wiki/Application:Novatool',
      py_modules = ['novatool',
                    'novacom',
                    'devicebutton',
                    'qt4reactor',
                    'resources',
                    'systeminfo',
                    'httpunzip/__init__'],
      data_files = ['build-info'],
      )