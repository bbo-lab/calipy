#!/usr/bin/env python3

from setuptools import setup

setup(
    name = "CaliPy",
    version = "0.1.0",
    description = "Camera Calibration Toolkit",
    author = "Florian Franzen",
    install_requires = [
        'imageio', # For file io (file)
        'pyqt', # For user inteface (ui)
        'pyyaml', # For meta data file (file)
        'numpy',
        'scipy',
        'pandas',
        #'seaborn',
        'construct' # To parse CCV headers
    ]
    packages=['multiview'],
    scripts=['cali.py'],
)
