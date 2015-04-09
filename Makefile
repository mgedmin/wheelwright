.PHONY: all
all: .install-stamp .install-stamp-py2

.PHONY: wheels
wheels: all
	@mkdir -p wheels
	bin/pip2 wheel -w wheels -r source-only.txt --no-deps
	bin/python3 wheelwright.py

.PHONY: clean
clean:
	rm -rf bin build include installers lib local wheels/*.whl .install-stamp .install-stamp-py2

bin/pip3: | bin/pip2
	virtualenv -p python3 .

bin/pip2:
	virtualenv -p python2 .

.install-stamp: requirements.txt | bin/pip3
	bin/pip3 install -r requirements.txt
	touch $@

.install-stamp-py2: requirements.txt | bin/pip2
	bin/pip2 install -r requirements.txt
	touch $@
