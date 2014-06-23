.PHONY: all
all: .install-stamp

.PHONY: wheels
wheels: all
	@mkdir -p wheels
	bin/pip2 wheel -w wheels -r source-only.txt --no-deps
	bin/python wheelwright.py
	bin/wheel convert -d wheels installers/*.exe installers/*.egg

.PHONY: clean
clean:
	rm -rf bin build include installers lib local wheels .install-stamp

bin/pip: | bin/pip2
	virtualenv -p python3 .

bin/pip2:
	virtualenv -p python .

.install-stamp: requirements.txt | bin/pip bin/pip2
	bin/pip install -r requirements.txt
	bin/pip2 install -r requirements.txt
	touch $@
