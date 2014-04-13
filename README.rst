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
