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
        self.announce(
            'Running command: %s' % ' '.join(command),
            level=log.INFO)
        subprocess.check_call(command)


setup(
    name = "CaliPy",
    version = "0.1.0",
    description = "Camera Calibration Toolkit",
    author = "Florian Franzen",
    install_requires = [
        'pyqt', # For user inteface (ui)
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
