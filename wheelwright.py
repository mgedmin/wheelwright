#!/usr/bin/env python

import glob
import logging
import os
import sys
import argparse
try:
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser

import requests


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


def create_wheels(installer_dir, wheel_dir):
    for filename in glob.glob(os.path.join(installer_dir, '*.exe')):
        # TODO: determine the name of the .whl
        # check if it already exists
        # if not, invoke bin/wheel convert -d ${wheel_dir} {filename}
        pass


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
        download_installers(packages, installer_dir, versions, formats)
        ensure_dir(wheel_dir)
        create_wheels(installer_dir, wheel_dir)
    except Error as e:
        sys.exit(str(e))


if __name__ == '__main__':
    main()
