#!/usr/bin/env python

import glob
import logging
import os
import sys
from ConfigParser import SafeConfigParser

import requests


PYPI_URL = 'https://pypi.python.org/pypi'


log = logging.getLogger(__name__)


class Error(Exception):
    pass


def load_config():
    config = SafeConfigParser()
    config.read(['packages.ini'])
    return config


def get_pypi_info(package_name):
    url = '%s/%s/json' % (PYPI_URL, package_name)
    response = requests.get(url)
    if not response:
        raise Error('Failed to fetch %s: %s %s' % (url, response.status_code, response.reason))
    return response.json()


def get_installer_urls(info):
    for url in info['urls']:
        if url['packagetype'] == 'bdist_wininst':
            yield url


def download_installers(packages, destdir):
    for pkg in packages:
        info = get_pypi_info(pkg)
        for url in get_installer_urls(info):
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


def set_up_logging():
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.INFO)


def ensure_dir(destdir):
    if not os.path.isdir(destdir):
        os.makedirs(destdir)


def main():
    set_up_logging()
    config = load_config()
    packages = config.get('wheelwright', 'packages').split()
    installer_dir = config.get('wheelwright', 'installer-dir', 'installers')
    wheel_dir = config.get('wheelwright', 'wheel-dir', 'wheels')
    try:
        ensure_dir(installer_dir)
        download_installers(packages, installer_dir)
        ensure_dir(wheel_dir)
        create_wheels(installer_dir, wheel_dir)
    except Error as e:
        print(e)


if __name__ == '__main__':
    main()
