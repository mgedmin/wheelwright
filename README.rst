My Little Wheelwright
=====================

This is a script that downloads binary Windows eggs of certain packages
from PyPI and converts them to binary Windows wheels.


Usage
-----

Run ``make wheels`` and you'll get a bunch of wheels in ``./wheels``,
for packages listed in ``packages.ini``.


Background
----------

I have a VM on Rackspace that suffers from some strange issue where SSL
connections mysteriously fail, but only when I use Python's httplib [1]_.
A side effect of this is that I cannot use zc.buildout to run zodbbrowser's
tests.  I'd like to use pip instead, but pip needs wheels instead of eggs.

.. [1] https://gist.github.com/mgedmin/7637559

As a workaround I set up a `Jenkins job <https://jenkins.gedmin.as/job/wheelwright/>`__
to convert .egg and .exe files to wheels that pip can use.  These are published
at https://debesis.gedmin.as/wheels/.  Then I told my Jenkins build script to ::

    set PIP_FIND_LINKS=https://debesis.gedmin.as/wheels/ 

and now `tox` can install things like `lxml` and `zope.interface`.


Pure-Python packages
--------------------

Some pure-Python packages also trip up the SSL bug, even when I use pip:
specifically, those packages that use setup_requires to depend on packages
not already installed.

Wheels can be built for these if you list them in ``source-only.txt``.
This is done by the Makefile, not by wheelwright.py, at the moment.


Future Plans
------------

Get upstreams to build binary wheels and put them up on PyPI for everyone!
There's an `open bug <https://github.com/zopefoundation/zope.wineggbuilder/issues/2>`__
for zope.wineggbuilder which is responsible for, well, actually, everything that *I* need:
`lxml`, `zope.interface`, ....
