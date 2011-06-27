#!/usr/bin/env python2

from distutils.core import setup
from zokket import get_version

kwargs = {
    'name': 'zokket',
    'version': get_version(),
    'license': 'BSD',
    'author': 'Kyle Fuller',
    'author_email': 'inbox@kylefuller.co.uk',
    'packages': ['zokket'],
    'download_url': 'http://github.com/kylef/zokket/zipball/%s' % get_version(),
}

setup(**kwargs)
