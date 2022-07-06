#!/usr/bin/env python3

from setuptools import setup
from distutils import cmd, log
import subprocess


class PyInstallerCommand(cmd.Command):
    """A custom command to package CaliPy with PyInstaller"""

    description = 'Create standalone version using PyInstaller'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        command = ['pyinstaller', '-n', 'CaliPy', '-w', 'cali.py']
        self.announce("Running command: {}".format(' '.join(command)), level=log.INFO)
        subprocess.check_call(command)


setup(
    entry_points={
        "gui_scripts": ["calipy = calipy.main:main"],
    },
    cmdclass={
        "standalone": PyInstallerCommand,
    },
    data_files=[
        ('share/applications', ['de.caesar.bbo.CaliPy.desktop']),
    ],
)
