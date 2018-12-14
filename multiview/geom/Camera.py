from . import Projection
from . import ImagePoint
from .Transform import SimilarityTransform

import numpy as np
import cv2

class Camera(Projection):
    """
    A projection with distortion based on the OpenCV camera model

    R is the rotation matrix
    t is the translation vector
    A is the internal projection matrix
    k is the distortion vector
    """

    def __init__(self, basis, R, t, A, k):
        Projection.__init__(self, basis, R, t, A)

        self._k = k

    def __repr__(self):
        t = self.getTransform(self.basis).t
        return "<camera at x: {}, y: {}, z: {}>".format(*t)

    @property
    def k(self):
        """The translation"""
        return self._k

    @property
    def fx(self):
        """focal length x"""
        return self._A[0,0]

    @property
    def fy(self):
        """focal length y"""
        return self._A[1,1]

    @property
    def cx(self):
        """optical center x"""
        return self._A[0,2]

    @property
    def cy(self):
        """optical center y"""
        return self._A[1,2]

    def clone(self):
        return Camera(self._basis, self._R, self._t, self._A, self._k)

    def newImagePoint(self, x_d, y_d):
        """Return new image point"""

        x, y = self._undistort(x_d, y_d)

        return ImagePoint(self, x, y, x_d, y_d)

    def project(self, point):
        """Project 3D coordinate to image point"""

        # Run project of parent
        projection = Projection.project(self, point)

        # Add distorted point info to result
        xd, yd = self._distort(projection.x, projection.y)

        projection._xd = xd
        projection._yd = yd

        return projection

    def rebase(self, to):
        """
        Rebase to other coordinate system

        Returns rebased clone
        """
        transform = to.getTransform(self, self.basis)

        R = transform.R
        t = transform.t

        # Correct for similarity transform FixMe?
        if type(transform) is SimilarityTransform:
            t /= transform.s

        return Camera(to, R, t, self.A, self.k)

    def _distort(self, x, y):
        """Distort camera point"""
        # To relative coordinates
        x2 = (x - self.cx)/ self.fx
        y2 = (y - self.cy)/ self.fy

        # Apply distortion
        point, _ = cv2.projectPoints(np.array([[[x2, y2, 1.0]]]), np.zeros(3), np.zeros(3), self.A, self.k)

        return point[0,0,0], point[0,0,1]

    def _undistort(self, xd, yd):
        """Undistort camera point"""

        point = cv2.undistortPoints(np.array([[[xd, yd]]]), self.A, self.k, None, self.A)

        return point[0,0,0], point[0,0,1]
