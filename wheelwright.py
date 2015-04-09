#!/usr/bin/env python3
"""
Download binary egg/exe packages from PyPI and convert them to wheels.

Reads packages.ini for a list of packages.  The format of the INI file is

    [wheelwright]
    # list of package names to process
    packages = ...

    # where to put downloaded binary packages
    installer-dir = ...

    # where to put converted wheels
    wheel-dir = ...

    # every package can be optionally configured like this:
    [pkg:name]
    # versions to process (e.g. if new versions have whl files on PyPI,
    # but old ones have only .egg/.exe installers you may list all the
    # old versions you want to support here)
    versions = ...
    # installer formats to download, defaults to bdist_wininst
    formats = ...

"""

import glob
import logging
import os
import sys
import argparse
from configparser import SafeConfigParser

import requests
import wheel.tool
import wheel.wininst2wheel
from wheel.egg2wheel import egg_info_re
# In case this changes later: wheel.egg2wheel defines
#   egg_info_re = re.compile(r'(?P<name>.+?)-(?P<ver>.+?)(-(?P<pyver>.+?))?(-(?P<arch>.+?))?.egg', re.VERBOSE)


PYPI_URL = 'https://pypi.python.org/pypi'


log = logging.getLogger(__name__)


class Error(Exception):
    pass


def load_config(config_file='packages.ini'):
    config = SafeConfigParser()
    config.read([config_file])
    return config


def get_pypi_info(package_name, version):
    if version:
        url = '%s/%s/%s/json' % (PYPI_URL, package_name, version)
    else:
        url = '%s/%s/json' % (PYPI_URL, package_name)
    log.debug("Fetching %s", url)
    response = requests.get(url)
    if not response:
        raise Error('Failed to fetch %s: %s %s' % (url, response.status_code, response.reason))
    return response.json()


def get_installer_urls(info, formats):
    if not formats:
        formats = ['bdist_wininst']
    for url in info['urls']:
        if url['packagetype'] in formats:
            yield url


def download_installers(packages, destdir, versions={}, formats={}):
    for pkg in packages:
        for version in versions.get(pkg) or [None]:
            info = get_pypi_info(pkg, version)
            for url in get_installer_urls(info, formats.get(pkg)):
                filename = os.path.join(destdir, url['filename'])
                if not os.path.exists(filename):
                    download(url['url'], filename)


def download(url, filename):
    response = requests.get(url)
    if not response:
        raise Error('Failed to download %s: %s %s' % (url, response.status_code, response.reason))
    log.info("Downloading %s" % url)
    with open(filename + '.tmp', 'wb') as f:
        for chunk in response.iter_content(64 * 1024):
            f.write(chunk)
    os.rename(filename + '.tmp', filename)


def find_installers(installer_dir):
    return (glob.glob(os.path.join(installer_dir, '*.exe')) +
            glob.glob(os.path.join(installer_dir, '*.egg')))


def name_of_corresponding_wheel(installer):
    filename = os.path.basename(installer)
    if filename.endswith('.egg'):
        # e.g. installers/ZODB3-3.10.5-py2.7-win-amd64.egg becomes
        # e.g. wheels/ZODB3-3.10.5-cp27-none-win_amd64.whl
        info = egg_info_re.match(filename).groupdict()
        dist_info = "{name}-{ver}".format(**info)
        abi = 'none'
        pyver = info['pyver'].replace('.', '')
        arch = (info['arch'] or 'any').replace('.', '_').replace('-', '_')
        if arch != 'any':
            # assume all binary eggs are for CPython
            pyver = 'cp' + pyver[2:]
        wheel_name = '-'.join((dist_info, pyver, abi, arch))
        return wheel_name + '.whl'
    if filename.endswith('.exe'):
        # Not passing egginfo_name to parse_info() is wrong, but works on
        # the packages I care about.
        info = wheel.wininst2wheel.parse_info(filename, None)
        dist_info = "{name}-{ver}".format(**info)
        abi = 'none'
        pyver = info['pyver']
        arch = (info['arch'] or 'any').replace('.', '_').replace('-', '_')
        if arch != 'any':
            pyver = pyver.replace('py', 'cp')
        wheel_name = '-'.join((dist_info, pyver, abi, arch))
        return wheel_name + '.whl'


def create_wheels(installer_dir, wheel_dir, verbose=False):
    n = 0
    for filename in sorted(find_installers(installer_dir)):
        basename = os.path.basename(filename)
        wheel_filename = name_of_corresponding_wheel(filename)
        if not wheel_filename:
            log.debug("Skipping %s (couldn't parse the filename)", basename)
            continue
        wheel_pathname = os.path.join(wheel_dir, wheel_filename)
        if os.path.exists(wheel_pathname):
            log.debug('Skipping %s (%s exists)', basename, wheel_filename)
            continue
        convert_to_wheel(filename, wheel_dir, wheel_filename, verbose=verbose)
        n += 1
    if n:
        log.info('Created %d wheels', n)
    else:
        log.info("Everything's up to date")


def convert_to_wheel(filename, wheel_dir, wheel_filename, verbose=False):
    if verbose:
        sys.stdout.write('Converting ')
    wheel.tool.convert([filename], wheel_dir, verbose=verbose)


def set_up_logging(level=logging.INFO):
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(level)


def ensure_dir(destdir):
    if not os.path.isdir(destdir):
        os.makedirs(destdir)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch binary packages from PyPI and build wheels for them")
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--config-file', default='packages.ini')
    parser.add_argument('--no-download', action='store_false', dest='download', default=True,
                        help='skip the downloading, just convert installers already in place')
    args = parser.parse_args()
    set_up_logging(logging.DEBUG if args.verbose else logging.INFO)
    config = load_config(args.config_file)
    packages = config.get('wheelwright', 'packages').split()
    versions = {}
    formats = {}
    for pkg in packages:
        if config.has_section('pkg:' + pkg):
            versions[pkg] = config.get('pkg:' + pkg, 'versions', fallback='').split()
            formats[pkg] = config.get('pkg:' + pkg, 'formats', fallback='').split()
    installer_dir = config.get('wheelwright', 'installer-dir', fallback='installers')
    wheel_dir = config.get('wheelwright', 'wheel-dir', fallback='wheels')
    try:
        ensure_dir(installer_dir)
        if args.download:
            download_installers(packages, installer_dir, versions, formats)
        ensure_dir(wheel_dir)
        create_wheels(installer_dir, wheel_dir, verbose=args.verbose)
    except Error as e:
        sys.exit(str(e))


if __name__ == '__main__':
    main()
