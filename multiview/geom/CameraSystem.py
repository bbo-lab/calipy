from .Basis import Basis

from .Camera import Camera

from ..file.Path import Path

import numpy as np

class CameraSystem(Basis):
    def __init__(self):
        """Create an new Camera System"""
        Basis.__init__(self)

    def newCamera(self, R, t, A, k):
        """Create new camera for coordinate system"""
        return Camera(self, R, t, A, k)

    @staticmethod
    def fromPath(path):
        """Load calib from mv.file.Path object"""
        return CameraSystem.fromCalNpz(path.ofCalNpz())

    @staticmethod
    def fromCalNpz(filename):
        """Load from .cal.npz file"""

        # Load from file
        calib = np.load(filename)

        # Parse dictionary
        basis = CameraSystem()

        cameras = []

        cam_count = calib['A_fit'].shape[0]
        for cam_id in range(cam_count):
            R = calib['RX1_fit'][cam_id]

            t = calib['tX1_fit'][cam_id]

            # ToDo: Move conversion to milimeter to calibration
            t *= 37

            a = calib['A_fit'][cam_id]

            A = np.eye(3)
            A[0,0] = a[0] # fx
            A[1,1] = a[2] # fy

            A[0,2] = a[1] # cx
            A[1,2] = a[3] # cy

            k = calib['k_fit'][cam_id]

            cameras.append(basis.newCamera(R, t, A, k))

        return basis, cameras
