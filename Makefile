all: .install-stamp

wheels: all
	bin/python wheelwright.py
	bin/wheel convert -d wheels installers/*.exe installers/*.egg

bin/pip:
	virtualenv .

.install-stamp: requirements.txt | bin/pip
	bin/pip install -r requirements.txt
	touch $@
