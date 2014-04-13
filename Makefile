all: .install-stamp

bin/pip:
	virtualenv .

.install-stamp: requirements.txt | bin/pip
	bin/pip install -r requirements.txt
	touch $@
