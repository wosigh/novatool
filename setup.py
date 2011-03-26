#!/usr/bin/env python

import subprocess
from distutils.core import setup
from distutils.command.build import build as _build

class build(_build):
    user_options= _build.user_options
    def run(self):
        if subprocess.call(['make','deps']) == 0:
            _build.run(self)

setup(name = 'novatool',
      cmdclass = {'build' : build},
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