#!/usr/bin/env python3

from setuptools import setup

setup(
    name = "CaliPy",
    version = "0.1.0",
    description = "Camera Calibration Toolkit",
    author = "Florian Franzen",
    install_requires = [
        'pyqt', # For user inteface (ui)
        'pyqtgraph',
        'numpy',
        'scipy',
        'pyyaml', # For meta data file (file)
        'imageio', # For file io (file)
        'construct' # To parse CCV headers
    ],
    packages=['calipy'],
    scripts=['cali.py'],
)
