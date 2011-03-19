from distutils.core import setup
import py2exe

py2exe_options = dict(
    ascii = True,
    excludes = ['_ssl','pyexpat','bz2'],
    bundle_files = True,
    compressed = True,
    dll_excludes = ['MSVCP90.dll']
)

setup(
    windows = [
        {
            'script': 'novatool.py',
            'icon_resources': [(1, 'novacomInstaller.ico')]
        }
    ],
    options = {'py2exe': py2exe_options},
    zipfile = None,
    description = 'Cross-platform novacom tool',
    author = 'Webos-Internals',
    maintainer = 'Ryan Hope',
    maintainer_email = 'rmh3093@gmail.com',
    version = '1.0',
    name = 'Novatool'
)
