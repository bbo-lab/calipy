#!/usr/bin/env python3

from setuptools import setup
from distutils import cmd, log
import subprocess

from calipy import VERSION


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
    name = "CaliPy",
    version = VERSION,
    description = "Camera Calibration Application",
    author = "Florian Franzen",
    install_requires = [
        'pyqt5', # For user inteface (ui)
        'pyqtgraph', # For user interface (ui)
        'numpy',
        'scipy',
        'opencv-contrib-python', # Core functionality (calib, detect, etc)
        'pyyaml', # For Meta data file (metaio)
        'imageio', # For video file io (rawio)
        'construct' # To parse CCV headers (rawio)
    ],
    packages = ['calipy'],
    entry_points = {"gui_scripts": ["calipy = calipy.main:main"]},
    cmdclass = {"standalone": PyInstallerCommand},
)
