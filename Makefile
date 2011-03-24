all:
	pyrcc4 resources.qrc > resources.py
	translate.sh