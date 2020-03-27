#!/usr/bin/env python3

from distutils.core import setup
from distutils.command.install import install


class Install(install):
    def run(self):
        # Run normal install
        install.run(self)
        # Post-install setup
        from ibtracs import initial_setup
        initial_setup()

setup(
    name='ibtracs',
    version='1.0',
    author='Levi Cowan',
    license='MIT',
    packages=['ibtracs'],
    cmdclass={'install': Install}
)
