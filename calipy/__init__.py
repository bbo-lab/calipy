# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

VERSION = "2.0.0-alpha0"

# Always at least provide VERSION
try:
  from . import core, ui, metaio, calib, detect, math
  from .main import main
except ImportError:
    pass


