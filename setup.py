#!/usr/bin/env python3

from distutils.core import setup
from distutils.command.install import install
from subprocess import Popen, PIPE, STDOUT
import os, sys


class Install(install):
    def run(self):
        install.run(self)
        #  self.post_install()

    def post_install(self):
        # Run script from directory where setup.py was called (the git repo).
        # This avoids relative import problems because the script is outside
        # the package in the git repo.
        scriptname = os.path.join(os.path.dirname(__file__), 'initial_setup.py')
        p = Popen([sys.executable, scriptname], stdout=PIPE, stderr=STDOUT)
        line = bytearray()
        while True:
            char = p.stdout.read(1)
            if not char:
                break
            line += char
            if char in (b'\r', b'\n'):
                print(line.decode(), end='')
                line = bytearray()
        p.wait()


setup(
    name='ibtracs',
    version='1.0',
    author='Levi Cowan',
    license='MIT',
    packages=['ibtracs'],
    #  scripts=['initial_setup.py'],
    cmdclass={'install': Install}
)
