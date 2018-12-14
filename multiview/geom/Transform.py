import numpy as np

class RidgidBodyTransform:
    def __init__(self, R, t):
        self._R = R
        self._t = t

    @property
    def R(self):
        """Rotation matrix of transformation"""
        return self._R

    @property
    def t(self):
        """Translation vector of transformation"""
        return self._t

    def clone(self):
        return RidgidBodyTransform(self._R, self._t)

    def toMatrix(self):
        M = np.eye(4)

        M[0:3, 0:3] = self._R
        M[0:3,   3] = self._t

        return M

    def invert(self):
        inverted = self.clone()

        inverted._R = self._R.T
        inverted._t = -np.dot(self._R.T, self._t)

        return inverted

    def __matmul__(f, g):
        """Returns f of g, (x->y,y->z)->(x->z) or f(g(x))."""

        # Transformations have to be off same type to avoid information loss
        if type(f) != type(g):
            if type(f) == RidgidBodyTransform:
                # Upgrade f and try again
                f = g.fromRidgidBody(f)
                return f @ g
            else:
                raise "No fix known!"

        # Combine transformations
        fog = f.clone()
        fog._R = np.dot(f.R, g.R)
        fog._t = np.dot(f.R, g.t) + f.t

        return fog

    def apply(self, X):
        X = np.atleast_2d(X)

        return np.dot(self._R, X.T).T + self._t

class SimilarityTransform(RidgidBodyTransform):
    """
    A similarity transform
    """

    def __init__(self, s, R, t):
        RidgidBodyTransform.__init__(self, R, t)
        self._s = s

    @staticmethod
    def fromRidgidBody(other):
        return SimilarityTransform(1.0, other.R, other.t)

    @property
    def s(self):
        """Scaling scalar of transformation"""
        return self._s

    def clone(self):
        return SimilarityTransform(self.s, self.R, self.t)

    def toMatrix(self):
        M = RidgidBodyTransform.toMatrix(self)

        return self.s * M

    def invert(self):
        inverted = RidgidBodyTransform.invert(self)

        inverted._s = 1.0 / self.s

        inverted._t *= inverted.s

        return inverted

    def __matmul__(f, g):
        """Returns f of g, (x->y,y->z)->(x->z) or f(g(x))."""

        # Upgrade type if necessary
        if type(g) is RidgidBodyTransform:
            g = SimilarityTransform.fromRidgidBody(g)

        # Combine transformations
        fog = f.clone()
        fog._s = f.s * g.s
        fog._R = np.dot(f.R, g.R)
        fog._t = f.s * np.dot(f.R, g.t) + f.t

        return fog

    def apply(self, X):
        X = np.atleast_2d(X)

        return self.s * np.dot(self.R, X.T).T + self.t
