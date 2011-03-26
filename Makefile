.PHONY: build-info resources

help:
	@echo "Valid options are: macosx windows linux"

all: clean sdist macosx windows linux

clean:
	@rm -rf build dist build-info resources.py MANIFEST
	
resources:
	@pyside-rcc resources.qrc > resources.py
	
build-info:
	@git describe --dirty --always > build-info
	
deps: build-info resources
	
sdist: deps
	@python setup/setup.py sdist

windows: deps
	rm -rf dist/windows
	wine ~/.wine/drive_c/Python26/python.exe setup/setup-cx.py build
	cp ~/.wine/drive_c/Python26/DLLs/python26.dll build/exe.win32-2.6/
	cp ~/.wine/drive_c/Python26/Lib/site-packages/PySide/QtCore4.dll build/exe.win32-2.6/
	cp ~/.wine/drive_c/Python26/Lib/site-packages/PySide/QtGui4.dll build/exe.win32-2.6/
	cp ~/.wine/drive_c/Python26/Lib/site-packages/PySide/pyside-python2.6.dll build/exe.win32-2.6/
	cp ~/.wine/drive_c/Python26/Lib/site-packages/PySide/shiboken-python2.6.dll build/exe.win32-2.6/
	mkdir -p dist/windows
	wine ~/.wine/drive_c/Program\ Files\ \(x86\)/Inno\ Setup\ 5/ISCC.exe win-installer.iss
	mv dist/windows/NovatoolSetup.exe dist/windows/NovatoolSetup-`cat build-info`.exe

linux: deps

macosx: deps
	rm -rf dist/macosx
	/opt/local/bin/python2.6 setup/setup-cx.py build
	mkdir -p dist/macosx/novatool.app/Contents
	mkdir dist/macosx/novatool.app/Contents/MacOS
	mkdir dist/macosx/novatool.app/Contents/Resources
	cp novacomInstaller.icns dist/macosx/novatool.app/Contents/Resources
	cp Info.plist dist/macosx/novatool.app/Contents/
	echo "APPL????" > dist/macosx/novatool.app/Contents/PkgInfo
	mv build/exe.macosx-10.6-*-2.6/novatool dist/macosx/novatool.app/Contents/MacOS/
	mv build/exe.macosx-10.6-*-2.6/*.dylib dist/macosx/novatool.app/Contents/MacOS/
	mv build/exe.macosx-10.6-*-2.6/PySide* dist/macosx/novatool.app/Contents/MacOS/
	mv build/exe.macosx-10.6-*-2.6/*.zip dist/macosx/novatool.app/Contents/MacOS/
	morelibs=`ls build/exe.macosx-10.6-*-2.6`
	/opt/local/bin/macdeployqt dist/macosx/novatool.app
	cd dist/macosx/novatool.app/Contents/Frameworks; \
	rm -rf QtDeclarative.framework; \
	rm -rf QtNetwork.framework; \
	rm -rf QtScript.framework; \
	rm -rf QtSql.framework; \
	rm -rf QtSvg.framework; \
	rm -rf QtXmlPatterns.framework
	cd dist/macosx/novatool.app/Contents/MacOS; \
	rm libQtCore.4.dylib; \
	rm libQtGui.4.dylib; \
	install_name_tool -change /opt/local/lib/libQtCore.4.dylib @executable_path/../Frameworks/QtCore.framework/Versions/4/QtCore PySide.QtCore.so; \
	install_name_tool -change /opt/local/lib/libQtGui.4.dylib @executable_path/../Frameworks/QtGui.framework/Versions/4/QtGui PySide.QtGui.so; \
	install_name_tool -change /opt/local/lib/libQtCore.4.dylib @executable_path/../Frameworks/QtCore.framework/Versions/4/QtCore PySide.QtGui.so; \
	install_name_tool -change /opt/local/lib/libQtCore.4.dylib @executable_path/../Frameworks/QtCore.framework/Versions/4/QtCore libpyside-python2.6.1.0.dylib; \
	for f in `ls *.so`; do \
		libs=`otool -XL $$f | grep "/opt/local/lib" | cut -f 2 | cut -f 1 -d " "`; \
 		if [[ -n $$libs ]]; then \
  			for l in $$libs; do \
   				ll=`echo $$l | cut -f 5 -d"/"`; \
   				install_name_tool -change $$l @executable_path/$$ll $$f; \
  			done; \
 		fi; \
	done; \
	for f in `ls *.dylib`; do \
		install_name_tool -id @executable_path/$$f $$f; \
		libs=`otool -XL $$f | grep "/opt/local/lib" | cut -f 2 | cut -f 1 -d " "`; \
 		if [[ -n $$libs ]]; then \
  			for l in $$libs; do \
   				ll=`echo $$l | cut -f 5 -d"/"`; \
   				install_name_tool -change $$l @executable_path/$$ll $$f; \
  			done; \
 		fi; \
	done
	mv build/exe.macosx-10.6-*-2.6/* dist/macosx/novatool.app/Contents/MacOS/
	cd dist/macosx/novatool.app/Contents/MacOS; \
	for f in $$morelibs; do \
		libs=`otool -XL $$f | grep "/opt/local/lib" | cut -f 2 | cut -f 1 -d " "`; \
 		if [[ -n $$libs ]]; then \
  			for l in $$libs; do \
   				ll=`echo $$l | cut -f 5 -d"/"`; \
   				install_name_tool -change $$l @executable_path/$$ll $$f; \
  			done; \
 		fi; \
	done
	cd extra_mod; \
	python -m py_compile *.py; \
	zip -u ../dist/macosx/novatool.app/Contents/MacOS/library.zip _scproxy.pyc _md5.pyc _sha.pyc _sha256.pyc _sha512.pyc
	mv dist/macosx/novatool.app dist/macosx/Novatool.app
	sh create-dmg/create-dmg --window-pos 400 400 --window-size 384 224 --volname Novatool dist/macosx/Novatool.dmg dist/macosx/Novatool.app
	rm -rf dist/macosx/Novatool.app
	mv dist/macosx/Novatool.dmg dist/macosx/Novatool-`cat build-info`.dmg