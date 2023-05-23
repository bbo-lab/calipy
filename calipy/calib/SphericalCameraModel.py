# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from .CameraModel import CameraModel


class SphericalCameraModel(CameraModel):
    ID = "opencv-omnidir"
    NAME = "Spherical Camera"

    def __init__(self, context):
        super().__init__(context)
