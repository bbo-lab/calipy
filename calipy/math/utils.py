# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import autograd.numpy as np

import scipy

from scipy import linalg


# pts.shape = (n, 1, 3)
def are_points_on_line(pts):
    """ Test all supplied points lay on one line """
    # Two points are always on a line
    if len(pts) < 3:
        return True

    # Center first two dimensions around first point
    pts = pts[1:, :, :2] - pts[0, :, :2]

    # Check if cross product with second point is zero
    return np.allclose(np.cross(pts[0, :, :], pts[1:, :, :]), 0.0)

# r.shape = (1,3)
def rodrigues_2rotmat_single(r):
    """ Calculate rotataion matrix from rodrigues vector """

    theta = np.power(r[0]**2 + r[1]**2 + r[2]**2, 0.5)
    u = r / (theta + -np.abs(np.sign(theta)) + 1)
    # row 1
    rotmat_00 = np.cos(theta) + u[0]**2 * (1 - np.cos(theta))
    rotmat_01 = u[0] * u[1] * (1 - np.cos(theta)) - u[2] * np.sin(theta)
    rotmat_02 = u[0] * u[2] * (1 - np.cos(theta)) + u[1] * np.sin(theta)

    # row 2
    rotmat_10 = u[0] * u[1] * (1 - np.cos(theta)) + u[2] * np.sin(theta)
    rotmat_11 = np.cos(theta) + u[1]**2 * (1 - np.cos(theta))
    rotmat_12 = u[1] * u[2] * (1 - np.cos(theta)) - u[0] * np.sin(theta)

    # row 3
    rotmat_20 = u[0] * u[2] * (1 - np.cos(theta)) - u[1] * np.sin(theta)
    rotmat_21 = u[1] * u[2] * (1 - np.cos(theta)) + u[0] * np.sin(theta)
    rotmat_22 = np.cos(theta) + u[2]**2 * (1 - np.cos(theta))

    rotmat = np.array([[rotmat_00, rotmat_01, rotmat_02],
                       [rotmat_10, rotmat_11, rotmat_12],
                       [rotmat_20, rotmat_21, rotmat_22]])

    return rotmat

# R.shape = (3,3)
def rotmat_2rodrigues_single(R):
    """ Calculate rodrigues vector from rotation matrix """

    r = np.zeros((3, 1), dtype=float)
    K = (R - R.T) / 2
    r[0] = K[2, 1]
    r[1] = K[0, 2]
    r[2] = K[1, 0]

    if not(np.all(R == np.identity(3))):
        R_logm = linalg.logm(R)
        theta_M_1 = R_logm[2, 1] / (r[0] + np.equal(r[0], 0.0))
        theta_M_2 = R_logm[0, 2] / (r[1] + np.equal(r[1], 0.0))
        theta_M_3 = R_logm[1, 0] / (r[2] + np.equal(r[2], 0.0))
        theta_M = np.array([theta_M_1, theta_M_2, theta_M_3])

        theta = np.mean(theta_M[theta_M != 0.0])
        r *= theta

    return r

# r.shape = (n,3)
def rodrigues_2rotmat(r):
    """Calucalte rotataion matrices from rodrigues vectors"""
    # output.shape = (n,3,3)

    num_vecs = r.shape[0]
    theta = np.power(r[:, 0]**2 + r[:, 1]**2 + r[:, 2]**2, 0.5)
    u = r / (theta + -np.abs(np.sign(theta)) + 1).reshape(num_vecs, 1)
    # row 1
    rotmat_00 = np.cos(theta) + u[:, 0]**2 * (1 - np.cos(theta))
    rotmat_01 = u[:, 0] * u[:, 1] * (1 - np.cos(theta)) - u[:, 2] * np.sin(theta)
    rotmat_02 = u[:, 0] * u[:, 2] * (1 - np.cos(theta)) + u[:, 1] * np.sin(theta)
    rotmat_0 = np.concatenate([rotmat_00.reshape(num_vecs, 1, 1),
                               rotmat_01.reshape(num_vecs, 1, 1),
                               rotmat_02.reshape(num_vecs, 1, 1)], 2)

    # row 2
    rotmat_10 = u[:, 0] * u[:, 1] * (1 - np.cos(theta)) + u[:, 2] * np.sin(theta)
    rotmat_11 = np.cos(theta) + u[:, 1]**2 * (1 - np.cos(theta))
    rotmat_12 = u[:, 1] * u[:, 2] * (1 - np.cos(theta)) - u[:, 0] * np.sin(theta)
    rotmat_1 = np.concatenate([rotmat_10.reshape(num_vecs, 1, 1),
                               rotmat_11.reshape(num_vecs, 1, 1),
                               rotmat_12.reshape(num_vecs, 1, 1)], 2)

    # row 3
    rotmat_20 = u[:, 0] * u[:, 2] * (1 - np.cos(theta)) - u[:, 1] * np.sin(theta)
    rotmat_21 = u[:, 1] * u[:, 2] * (1 - np.cos(theta)) + u[:, 0] * np.sin(theta)
    rotmat_22 = np.cos(theta) + u[:, 2]**2 * (1 - np.cos(theta))
    rotmat_2 = np.concatenate([rotmat_20.reshape(num_vecs, 1, 1),
                               rotmat_21.reshape(num_vecs, 1, 1),
                               rotmat_22.reshape(num_vecs, 1, 1)], 2)

    rotmat = np.concatenate([rotmat_0,
                             rotmat_1,
                             rotmat_2], 1)

    return rotmat
