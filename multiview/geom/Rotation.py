import numpy as np

import scipy

import math


_EPS = np.finfo(float).eps * 4.0

class Rotation:
    def __init__(self, q0, q1, q2, q3):
        self._data = np.array([q0, q1, q2, q3])

    def toEuler(self):
        """Return Rodrigues vector representation"""
        print("NOT IMPLEMENTED YET")
        pass

    def toMatrix(self):
        """
        Return rotation matrix representation

        Author: Christoph Gohlke
        License: BSD
        URL: http://www.lfd.uci.edu/~gohlke/code/transformations.py
        """

        q = np.array(self._data, dtype=np.float64, copy=True)

        n = np.dot(q, q)
        if n < _EPS:
            return np.identity(4)

        q *= math.sqrt(2.0 / n)

        q = np.outer(q, q)

        return np.array([
            [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
            [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
            [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
            [ 0.0, 0.0, 0.0, 1.0]])

    def toRodrigues(self):
        """Return Rodrigues vector representation"""
        #See rodrigues2rotMat_single and rotMat2rodrigues_single
        # Or cv2.Rodrigues
        print("NOT IMPLEMENTED YET")
        pass

    def toQuaternions(self):
        """Return quaternion representation"""
        return self._data

    @staticmethod
    def fromMatrix(M):
        """
        Create rotation from roatation matrix

        Author: Christoph Gohlke
        License: BSD
        URL: http://www.lfd.uci.edu/~gohlke/code/transformations.py
        """
        m00 = M[0, 0]
        m01 = M[0, 1]
        m02 = M[0, 2]
        m10 = M[1, 0]
        m11 = M[1, 1]
        m12 = M[1, 2]
        m20 = M[2, 0]
        m21 = M[2, 1]
        m22 = M[2, 2]

        # Symmetric matrix K
        K = np.array([[m00-m11-m22, 0.0,         0.0,         0.0],
                      [m01+m10,     m11-m00-m22, 0.0,         0.0],
                      [m02+m20,     m12+m21,     m22-m00-m11, 0.0],
                      [m21-m12,     m02-m20,     m10-m01,     m00+m11+m22]])
        K /= 3.0

        # Quaternion is eigenvector of K that corresponds to largest eigenvalue
        w, V = np.linalg.eigh(K)
        q = V[[3, 0, 1, 2], np.argmax(w)]

        if q[0] < 0.0:
            np.negative(q, q)

        q0, q1, q2, q3 = q

        return Rotation(q0, q1, q2, q3)

    @staticmethod
    def fromQuaternions(q0, q1, q2, q3):
        return Rotation(q0, q1, q2, q3)


def rodrigues2matrix(r):
    """
    Author: Arne?
    """
    rotMat = np.zeros([3, 3], dtype=float)

    # Compute useful values
    theta = np.power(r[0]**2 + r[1]**2 + r[2]**2, 0.5)
    u = r / theta

    # row 1
    rotMat[0, 0] = np.cos(theta) + u[0]**2 * (1 - np.cos(theta))
    rotMat[0, 1] = u[0] * u[1] * (1 - np.cos(theta)) - u[2] * np.sin(theta)
    rotMat[0, 2] = u[0] * u[2] * (1 - np.cos(theta)) + u[1] * np.sin(theta)

    # row 2
    rotMat[1, 0] = u[0] * u[1] * (1 - np.cos(theta)) + u[2] * np.sin(theta)
    rotMat[1, 1] = np.cos(theta) + u[1]**2 * (1 - np.cos(theta))
    rotMat[1, 2] = u[1] * u[2] * (1 - np.cos(theta)) - u[0] * np.sin(theta)

    # row 3
    rotMat[2, 0] = u[0] * u[2] * (1 - np.cos(theta)) - u[1] * np.sin(theta)
    rotMat[2, 1] = u[1] * u[2] * (1 - np.cos(theta)) + u[0] * np.sin(theta)
    rotMat[2, 2] = np.cos(theta) + u[2]**2 * (1 - np.cos(theta))

    return rotMat


def matrix2rodrigues(R):
    """
    Author: Arne?
    """
    r = np.zeros((3, 1), dtype=float)

    K = (R - R.T) / 2

    r[0] = K[2, 1]
    r[1] = K[0, 2]
    r[2] = K[1, 0]

    if not(np.all(R == np.identity(3))):
        R_logm = scipy.linalg.logm(R)

        thetaM = np.zeros(3)

        thetaM[0] = R_logm[2, 1] / (r[0] + np.equal(r[0], 0.0))
        thetaM[1] = R_logm[0, 2] / (r[1] + np.equal(r[1], 0.0))
        thetaM[2] = R_logm[1, 0] / (r[2] + np.equal(r[2], 0.0))

        theta = np.mean(thetaM[thetaM != 0.0])

        r = r * theta

    return r
