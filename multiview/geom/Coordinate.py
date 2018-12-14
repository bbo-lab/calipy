import numpy as np

class Coordinate:
    """A point in 3D space in a certain coordinate system."""

    def __init__(self, basis, x, y, z):
        self._basis = basis

        self._data = np.array([x, y, z])

    def __repr__(self):
        return "<coordinate with x: {}, y: {}, z: {}>".format(self.x, self.y, self.z)

    @property
    def basis(self):
        """Return the coordinate system in which the point located"""
        return self._basis

    @property
    def x(self):
        """Return the x coordinate of the point"""
        return self._data[0]

    @property
    def y(self):
        """Return the y coordinate of the point"""
        return self._data[1]

    @property
    def z(self):
        """Return the y coordinate of the point"""
        return self._data[2]

    def clone(self):
        """Clone/deepcopy coordinate"""
        return Coordinate(self._basis, self.x, self.y, self.z)

    def toVector(self):
        return self._data

    def toHomogeneousVector(self):
        return np.append(self._data, 1.0)

    def distanceTo(self, other):
        """Compute Euclidean distance to other coordinate"""
        if self.basis != other.basis:
            raise ValueError("Supplied Coordinates have mismatching basis.")

        return np.linalg.norm(self._data - other._data)

    def rebase(self, to, over=None):
        """
        Rebase to other coordinate system

        Returns rebased clone
        """

        transform = self.basis.getTransform(to, over)
        rebased = transform.apply(self._data).squeeze()

        return Coordinate(to, *rebased)

    @classmethod
    def scatter(co, coords, plt, *args, **kwargs):
        M = co.toMatrix(coords);
        plt.scatter(M[:, 0], M[:, 1], M[:, 2], *args, **kwargs)

    @classmethod
    def plot(co, coords, plt, *args, **kwargs):
        M = co.toMatrix(coords);
        plt.plot(M[:, 0], M[:, 1], M[:, 2], *args, **kwargs)

    @staticmethod
    def _toMatrix(coords, vec_func, n_dim=3):
        """Helper to turn list of coordinate objects to matrix"""
        basis = coords[0].basis

        M = np.full([len(coords), n_dim], np.nan)

        for i, c in enumerate(coords):
            if basis is not c.basis:
                raise ValueError("Supplied Coordinates have mismatching basis.")

            M[i, :] = vec_func(c)

        return M

    @classmethod
    def toMatrix(co, coords):
        """Turn list of coordinates to matrix"""

        return co._toMatrix(coords, co.toVector)

    @classmethod
    def toHomogeneousMatrix(co, coords):
        """Turn list of coordinates to homogeneous matrix"""

        return co._toMatrix(coords, co.toHomogeneousVector, n_dim=4)
