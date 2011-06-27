from fabric.api import *
from zokket import get_version

@task
def tag():
    local('git tag %s' % get_version())

@task
def push():
    local('git push origin %s' % get_version())

@task
def upload():
    local('python2 setup.py sdist register upload')

@task
def release():
    tag()
    push()
    upload()

