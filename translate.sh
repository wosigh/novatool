#!/bin/sh

langs=(it de_CH en_US)

xgettext --language=Python --keyword=_ --output=novatool.pot novatool.py
for lang in ${langs[@]}; do
	msginit --no-translator --input=novatool.pot --locale=${lang}
	mkdir -p ${lang}/LC_MESSAGES
	msgfmt --output-file=${lang}/LC_MESSAGES/novatool.mo ${lang}.po
done