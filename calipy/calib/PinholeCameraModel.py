# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from .CameraModel import CameraModel


class PinholeCameraModel(CameraModel):
    ID = "opencv-pinhole"
    NAME = "Pinhole Camera"

    def __init__(self, context):
        super().__init__(context)
