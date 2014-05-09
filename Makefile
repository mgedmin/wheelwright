.PHONY: all
all: .install-stamp

.PHONY: wheels
wheels: all
	bin/python wheelwright.py
	bin/wheel convert -d wheels installers/*.exe installers/*.egg

.PHONY: clean
clean:
	rm -rf bin build include installers lib local wheels .install-stamp

bin/pip:
	virtualenv -p python3 .

.install-stamp: requirements.txt | bin/pip
	bin/pip install -r requirements.txt
	touch $@
