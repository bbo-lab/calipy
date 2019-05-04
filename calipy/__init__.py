# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

VERSION = "1.0.0-alpha0"

# Always at least provide VERSION
try:
  from . import core, ui, metaio, rawio, calib, detect, math
  from .main import main
except ImportError:
    pass


