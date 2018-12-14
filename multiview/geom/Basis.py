from .Coordinate import Coordinate
from .Transform import (RidgidBodyTransform, SimilarityTransform)

import numpy as np

class Basis:
    """A frame of reference object"""

    def __init__(self):
        self._similarities = {}

    def newCoordinate(self, x, y, z):
        """Create new coordinate in relation to this basis"""
        return Coordinate(self, x, y, z)

    def coordsFromMatrix(self, A):
        """Create point objects from matrix [n 3] of points"""

        assert A.shape[1] == 3

        points = []
        for row in A:
            points.append(Coordinate(self, *row))

        return points

    def coordsFromNpyFile(self, file_path):
        """Create coordinate objects from ref3 file"""
        return self.coordsFromMatrix(np.load(file_path))

    def coordsFromPath(self, path):
        """Create coordinate objects from path object"""
        return self.coordsFromNpyFile(path.ofRef3Npy())

    def newProjection(self, R, t, A):
        """Create new coordinate in relation to this basis"""
        from .Projection import Projection
        return Projection(self, R, t, A)

    def addTransform(self, to, transform):
        """Add transformation from this to other basis"""
        self._similarities[to] = transform
        to._similarities[self] = transform.invert()

    def addRidgidBodyTransform(self, to, R, t):
        transform = RidgidBodyTransform(R, t)
        self.addTransform(to, transform)

    def addSimilarityTransform(self, to, s, R, t):
        transform = SimilarityTransform(s, R, t)
        self.addTransform(to, transform)

    def hasTransformation(self, to):
        return to in self._similarities

    def removeTransform(self, to):
        self._similarities.pop(to, None)
        to._similarities.pop(self, None)

    def getTransform(self, to, over=None):
        """Return simularity transform to rebase to supplied system"""

        # No transformation need, return the identifty
        if self == to:
            return RidgidBodyTransform(np.eye(3), np.zeros(3))

        # Return any tranformation we have right away
        if self.hasTransformation(to):
            return self._similarities[to]

        # Try to use supplied basis (over) to create transformation
        if over is not None:
            if self.hasTransformation(over) and over.hasTransformation(to):
                trans_s2o = self.getTransform(over)
                trans_o2t = over.getTransform(to)

                # ToDo: Add transform to map here?

                return trans_o2t @ trans_s2o

        # Could not find a transformation
        raise LookupError("No transformation known!")
