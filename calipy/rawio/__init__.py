# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from imageio import formats

from .CamCommandoFormat import CamCommandoFormat

from .Filters import FILTERS


# Initiate and register CamCommandoFormat
_ccv_format_instance = CamCommandoFormat(
    "CamCommandoVideo",
    "Reads in BBO CamCommando videos",
    ".ccv",
    "I",  # Video only
)
formats.add_format(_ccv_format_instance)
