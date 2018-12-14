import numpy as np

class ImagePoint:
    """A undistorted 2D point that is a result of a projection of a 3D point."""

    def __init__(self, proj, x, y, xd = None, yd = None):

        self._projection = proj

        self._data = np.array([x, y])
        self._xd = xd
        self._yd = yd

    def __repr__(self):
        return "<image point with x: {}, y: {}>".format(self.x, self.y)

    @property
    def projection(self):
        """Return the projection to which the point belongs"""
        return self._projection

    @property
    def x(self):
        """Return the x coordinate of the point"""
        return self._data[0]

    @property
    def y(self):
        """Return the y coordinate of the point"""
        return self._data[1]

    @property
    def xd(self):
        """Return the x coordinate of the point"""
        return self._xd

    @property
    def yd(self):
        """Return the y coordinate of the point"""
        return self._yd

    def toVector(self):
        return self._data

    def toDistortedVector(self):
        return np.array([self._xd, self._yd])

    def toHomogeneousVector(self):
        return np.append(self._data, 1.0)

    @staticmethod
    def _toMatrix(points, vec_func, n_dim=2):
        """Helper to turn list of image points to matrix"""

        proj = points[0].projection

        M = np.full([len(points), n_dim], np.nan)

        for i, p in enumerate(points):
            if proj is not p.projection:
                raise ValueError("Supplied image points have mismatching base projections.")

            M[i, :] = vec_func(p)

        return M

    @classmethod
    def toMatrix(co, points):
        """Turn list of image points to matrix, using undistorted pixel coordinates."""

        return co._toMatrix(points, co.toVector)

    @classmethod
    def toDistortedMatrix(co, points):
        """Turn list of image points to matrix, using distorted pixel coordinates."""

        return co._toMatrix(points, co.toDistortedVector)

    @classmethod
    def toHomogeneousMatrix(co, points):
        """Turn list of image points to matrix, using distorted pixel coordinates."""

        return co._toMatrix(points, co.toHomogeneousVector, n_dim=3)

    @staticmethod
    def fromNpyFile(filename, cameras):
        """Read image point objects from npy file. SKIPS NAN ENTRIES!"""

        data = np.load(filename)

        n_points, n_cam, n_dim = data.shape

        if n_cam != len(cameras):
            raise ValueError("Number of Cameras mismatch")

        if n_dim != 2:
            raise ValueError("Image points can only have two dimensions")

        result = []
        for i, cam in enumerate(cameras):
            points = [cam.newImagePoint(x, y) for x, y in data[:, i, :] if not np.isnan(x) or not np.isnan(y)]
            result.append(points)

        return result

    @classmethod
    def fromPath(co, path, cameras):
        """Create image point objects from path object"""
        return co.fromNpyFile(path.ofRef2Npy(), cameras)
