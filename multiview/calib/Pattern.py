from ..geom.Basis import Basis
from ..file.Path import Path

import numpy as np

class Pattern(Basis):

    def __init__(self, basis, R, t, gridsize, width, height):
        Basis.__init__(self)

        self.addRidgidBodyTransform(basis, R, t)

        self._basis = basis
        self._width = width
        self._height = height

        # Create map that maps pattern id to a 3D coordinate
        self._positions = np.flipud(np.indices([1, height - 1, width - 1]).reshape(3, -1)).T + [1, 1, 0]
        self._positions *= gridsize

    def __repr__(self):
        t = self.getTransform(self._basis).t
        return "<pattern at x: {}, y: {}, z: {}>".format(*t)

    def getPositionCount(self):
        return (self._width - 1) * (self._height - 1)

    def getPositions(self, ids=None):

        if ids is None:
            return self._positions

        return self._positions[ids, :]

    def toCoordinates(self, basis, ids=None):
        """
        Rebase to other coordinate system

        Returns rebased clone
        """

        coords = self.getPositions(ids)

        M_coords = self.getTransform(basis).apply(coords)

        return basis.coordsFromMatrix(M_coords)

    @staticmethod
    def fromPath(path, basis, width, height):
        return Pattern.fromCalNpz(path.ofCalNpz(), basis, width, height)

    @staticmethod
    def fromCalNpz(filename, basis, width, height):

        # Load external calibration result
        data = np.load(filename)

        # ToDo: Read from file
        gridsize = 37

        return [Pattern(basis, R, gridsize * t, gridsize, width, height) for R, t in zip(data['R1_fit'], data['t1_fit'])]
