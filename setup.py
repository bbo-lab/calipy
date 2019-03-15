#!/usr/bin/env python3

from skbuild import setup

setup(
    name = "MultiView",
    version = "0.1.0",
    description = "Multiple View Toolkit",
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
    scripts=['scripts/mv-calib.py'],
    test_suite="tests",
    cmake_args=['-DCAMIO_WITH_PYLON:BOOL=ON']
)
