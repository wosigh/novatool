import sys
from cx_Freeze import setup, Executable

includes = []
excludes = ['ssl','OpenSSL','xml']
packages = []
path = []
icon = None
include_files = ['build-info']
zip_includes = []

base = None
if sys.platform == 'win32':
	base = 'Win32GUI'
	icon = 'novacomInstaller.ico'
elif sys.platform == 'darwin':
	zip_includes = ['_scproxy.pyc']
	path = sys.path + ["."]
	
Novatool = Executable(
	script = 'novatool.py',
	compress = True,
	base = base,
	copyDependentFiles = True,
	appendScriptToExe = False,
	appendScriptToLibrary = False,
	icon = icon,
	)

setup(
	version = '1.0',
	description = 'A useful tool for people with WebOS devices.',
	author = 'Ryan Hope',
	name = 'Novatool',
	options = {'build_exe': {
							'includes': includes,
							'excludes': excludes,
				 			'packages': packages,
			 				'path': path,
                 			'include_files': include_files,
                 			'zip_includes': zip_includes
				 }},
	executables = [Novatool]
	)
