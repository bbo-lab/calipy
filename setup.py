#!/usr/bin/env python3

from skbuild import setup

setup(
    name = "pymultiview",
    version = "0.1.0",
    description = "multiview toolkit",
    author = "Florian Franzen",
    packages=['multiview'],
#    scripts=['scripts/generateRenderParam.py',
#             'scripts/CoordinateEstimator.py',
#             'scripts/npy2npz.py'],
    test_suite="tests",
    cmake_args=['-DCAMIO_WITH_PYLON:BOOL=ON']
)
