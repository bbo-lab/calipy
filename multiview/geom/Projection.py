from .Basis import Basis
from .ImagePoint import ImagePoint
from .Transform import SimilarityTransform

import numpy as np

class Projection(Basis):
    """
    3D to 2D projection

    R is the rotation matrix
    t is the translation vector
    A is the internal projection matrix
    """

    def __init__(self, basis, R, t, A):
        Basis.__init__(self)

        basis.addRidgidBodyTransform(self, R, t)

        self._basis = basis

        self._A = A

    @property
    def basis(self):
        """Return the coordinate system"""
        return self._basis

    @property
    def R(self):
        """Rotation to basis system"""
        return self.basis.getTransform(self).R

    @property
    def t(self):
        """Translation to basis system"""
        return self.basis.getTransform(self).t

    @property
    def A(self):
        """The projection matrix"""
        return self._A

    def clone(self):
        """Clone/deepcopy projection"""
        transform = self.getTransform(self._basis)
        return Projection(self._basis, transform.R, transform.t, self._A)

    def newImagePoint(self, x, y):
        """Return new image point for projection"""
        return ImagePoint(self, x, y)

    def pointsFromMatrix(self, A):
        """Create point objects from matrix [n 2] of image points"""

        assert A.shape[1] == 2

        points = []
        for row in A:
            points.append(ImagePoint(self, *row))

        return points

    def pointsFromNpyFile(self, file_path):
        """Create image point objects from ref3 file"""
        return self.pointsFromMatrix(np.load(file_path))

    def pointsFromPath(self, path):
        """Create image point objects from path object"""
        return self.pointsFromNpyFile(path.ofRef2Npy())

    def toMatrix(self, basis = None):
        """
        Return projection matrix including roatation and translation

        M = A * [R | t]
        """

        if basis is None:
            basis = self.basis

        M = basis.getTransform(self).toMatrix()[0:3, :]
        return np.dot(self.A, M)

    def toCoordinate(self, basis = None):

        if basis is None:
            basis = self.basis

        t = self.getTransform(basis).t

        return basis.newCoordinate(*t)

    def project(self, point):
        """Project 3D points to image points"""

        # Apply projection to point
        result = np.dot(self.toMatrix(point.basis), point.toHomogeneousVector())

        # Return normalzed image point
        return ImagePoint(self, result[0] / result[2],  result[1] / result[2])

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

        return Projection(to, R, t, self.A)

    def plot(self, basis, plt, scale=5.0, label=None):
        # Get origin
        o = self.toCoordinate(basis)

        plt.scatter(o.x, o.y, o.z, c="k", marker="o")

        if label is not None:
            plt.text(o.x, o.y, o.z, label)

        # Calculate axis
        p_x = self.newCoordinate(scale, 0, 0).rebase(self.basis)
        p_y = self.newCoordinate(0, scale, 0).rebase(self.basis)
        p_z = self.newCoordinate(0, 0, scale).rebase(self.basis)

        plt.plot([o.x, p_x.x], [o.y, p_x.y], [o.z, p_x.z], 'r')
        plt.plot([o.x, p_y.x], [o.y, p_y.y], [o.z, p_y.z], 'g')
        plt.plot([o.x, p_z.x], [o.y, p_z.y], [o.z, p_z.z], 'b')
