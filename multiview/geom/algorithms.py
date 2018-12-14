from .Coordinate import Coordinate
from .ImagePoint import ImagePoint
from .Rotation import (rodrigues2matrix, matrix2rodrigues)

from scipy.optimize import minimize

from math import sqrt

import numpy as np

def findRidgidBodyTransform(pts_one, pts_two):
    """
    Align two coordinate systems to each other computing a rigid body transform
    from one to the other

    More details in "A procedure for determining rigid body transformation paramters", John Challis J. Biomechanics 1995

    Result is saved within object and can then be used by calling rebase on
    coordinates, projections, etc.
    """
    assert len(pts_one) == len(pts_two)

    # Preprocess object structure
    one = pts_one[0].basis
    P_one = Coordinate.toMatrix(pts_one)

    two = pts_two[0].basis
    P_two = Coordinate.toMatrix(pts_two)

    # Calculate centroid of each point cloud
    centroid_one = np.mean(P_one, axis=0)
    centroid_two = np.mean(P_two, axis=0)

    # Center both point clouds onto each other
    delta_one = P_one - centroid_one
    delta_two = P_two - centroid_two

    # Compute covariance and svd
    C = np.dot(delta_two.T, delta_one) / delta_one.shape[0]

    if np.linalg.matrix_rank(C) < 2:
        raise ValueError("Covariance matrix is colinear:\n{}".format(C))

    U, d, V_T = np.linalg.svd(C)

    # Correct for potential reflections
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(V_T) < 0:
        S[-1, -1] = -1

    # Compute transformation
    R = U.dot(S).dot(V_T)
    t = centroid_two - R.dot(centroid_one)

    # Register result
    one.addRidgidBodyTransform(two, R, t)

    # Compute and return error per point
    pts_one_rebase = [pt.rebase(two) for pt in pts_one]
    reproj_errors = [pt_one.distanceTo(pt_two) for pt_one, pt_two in zip(pts_one_rebase, pts_two)]

    return reproj_errors


def findSimilarityTransform(pts_one, pts_two):
    """
    Align two coordinate systems to each other computing a similarity transform
    from one to the other

    Result is saved within object and can then be used by calling rebase on
    coordinates, projections, etc.
    """

    assert len(pts_one) == len(pts_two)

    # Preprocess object structure
    one = pts_one[0].basis
    P_one = Coordinate.toMatrix(pts_one)

    two = pts_two[0].basis
    P_two = Coordinate.toMatrix(pts_two)

    # Calculate centroid of each point cloud
    centroid_one = np.mean(P_one, axis=0)
    centroid_two = np.mean(P_two, axis=0)

    # Center both point clouds onto each other
    delta_one = P_one - centroid_one
    delta_two = P_two - centroid_two

    # Compute covariance and SVD of covariance
    C = np.dot(delta_two.T, delta_one) / delta_one.shape[0]

    if np.linalg.matrix_rank(C) < 2:
        raise ValueError("Covariance matrix is colinear:\n{}".format(C))

    U, d, V_T = np.linalg.svd(C)

    # Correct for potential reflections
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(V_T) < 0:
        S[-1, -1] = -1

    # Compute transformation using SVD of covariance
    R = U.dot(S).dot(V_T)
    s = (d * S.diagonal()).sum() / (delta_one ** 2).sum(axis = 1).mean()
    t = centroid_two - s * R.dot(centroid_one)

    # Register result
    one.addSimilarityTransform(two, s, R, t)

    # Compute and return error per point
    pts_one_rebase = [pt.rebase(two) for pt in pts_one]
    reproj_errors = [pt_one.distanceTo(pt_two) for pt_one, pt_two in zip(pts_one_rebase, pts_two)]

    return reproj_errors


def findRidgidBodyTransformFrom2D(cams, points, coords):
    """
    Find rigid body tranform between basises using 2D-3D relation.

    Depends on theano, autodiff and downhill.
    """

    import theano
    import theano.tensor as TT

    from autodiff import Tracer

    import downhill

    # Retrieve basises
    basis = cams[0].basis
    other = coords[0].basis

    # Check input dimension and structure
    assert len(cams) == len(points)

    for cam, pts in zip(cams, points):
        # Make sure all cams have same basis
        assert cam.basis == basis
        # Make sure that first points come from camera
        assert pts[0].projection == cam
        assert len(pts) == len(coords)

    ## INITIALIZATION
    # Estimate 3D coords of points for initialization
    coords_of_points = [findCoordinateFromImagePoints(pts) for pts in zip(*points)]

    # Compute initialization using findRidgidBodyTransform(...)
    findRidgidBodyTransform(coords, coords_of_points)

    # Retrieve result
    trans = other.getTransform(basis)

    R_0 = trans.R
    r_0 = matrix2rodrigues(R_0).flatten()

    t_0 = trans.t

    # Cleanup
    other.removeTransform(basis)

    ## PREPARE DATA
    C_train = Coordinate.toMatrix(coords)

    P_train = np.zeros([len(coords), len(cams), 2])

    for i, pts in enumerate(points):
        P_train[:, i, :] = ImagePoint.toMatrix(pts)

    ## BUILD SYMBOLIC REPRESENTATION
    # Define variables
    r = theano.shared(r_0, name="r")
    t = theano.shared(t_0, name="t")

    # Define data
    C = TT.matrix() # N_Points x 3
    P = TT.tensor3() # N_Points x N_Cams x 2

    # Use autodiff to turn r (rod-vec) to R (mat)
    tracer = Tracer()
    R = tracer.trace(rodrigues2matrix, r)

    # Translate points into camera coordinate frame
    reproj = TT.dot(C, R.T) + t

    # Collect residuals for each camera
    all_err = []
    for i, cam in enumerate(cams):
        # Make sure all cams have the same basis
        assert basis == cam.basis

        # Project reprojected points into camera
        proj_h = TT.dot(TT.dot(reproj, cam.R.T) + cam.t, cam.A.T)

        # Turn homogeneous to regular coordinates
        proj = proj_h[:, 0:2] / proj_h[:, 2].reshape([-1, 1])

        # Compute pixel distance to image points
        err = (P[:, i, :] - proj).norm(2, axis=1)

        # Add points to list of residuals
        all_err.append(err)

    # The loss is the mean of all residuals
    loss = TT.mean(all_err)

    # Run minimization
    result = downhill.minimize(loss       = loss,
                               train      = [C_train, P_train],
                               inputs     = [C, P],
                               batch_size = -1) # No batches

    # Get optimized values
    r_fit = r.get_value()
    R_fit = rodrigues2matrix(r_fit)

    t_fit = t.get_value()

    # Register result
    other.addRidgidBodyTransform(basis, R_fit, t_fit)

    # Todo: Return per pixel error
    return result


def findCoordinateFromImagePoints(points):
    """
    Find 3D coordinate using 2D image points using linear triangulation.

    See Hartley and Zisserman (2003), Section 12.2
    """

    # ToDo: Make sure there is just one point per camera

    basis = points[0].projection.basis

    A = np.full([len(points) * 2, 4], np.nan)

    for i, point in enumerate(points):
        cam = point.projection

        # Make sure all points are in the same coordinate basis
        assert(cam.basis == basis)

        M = cam.toMatrix()

        A[i * 2,     :] = point.x * M[2,:] - M[0,:]
        A[i * 2 + 1, :] = point.y * M[2,:] - M[1,:]

    U, s, V = np.linalg.svd(A)

    coord = V[-1, 0:3] / V[-1,3]

    return Coordinate(basis, *coord)

def findCoordinateFromImagePoints2(points):

    basis = points[0].projection.basis

    nCameras = len(points)

    n = np.zeros((nCameras, 3))
    m = np.zeros((nCameras, 3))

    for i_cam, point in enumerate(points):
        cam = point.projection

        # Make sure all points are in the same coordinate basis
        assert(cam.basis == basis)

        line = point.asHomogeneous().reshape(3, 1) * np.linspace(int(0), int(50), int(2))

        A_1 = np.linalg.lstsq(cam.A, np.identity(3))[0]

        line = np.dot(A_1, line)

        line = np.dot(cam.R.T, line - cam.t.reshape(3, 1))

        n[i_cam] = line[:, 0]
        m[i_cam] = line[:, 1] - line[:, 0]


    def obj_func(x):
        f = 0
        for i_cam in range(nCameras):
            res = (x[i_cam] * m[i_cam] + n[i_cam]) - x[-3:]
            f = f + np.dot(res, res)
        return 0.5 * f

    def obj_func_jac(x):
        jac = np.zeros(nCameras + 3)
        eq = 0
        for i_cam in range(nCameras):
            jac[i_cam] = np.dot(m[i_cam], m[i_cam]) * x[i_cam] + \
                         np.dot(m[i_cam], n[i_cam]) - \
                         np.dot(m[i_cam], x[-3:])
            eq = eq + (m[i_cam] * x[i_cam] + n[i_cam])
        jac[-3:] = nCameras * x[-3:] - eq
        return jac


    x0 = np.zeros(nCameras + 3)
    tolerance = np.finfo(np.float64).eps
    min_result = minimize(obj_func,
                          x0,
                          method='l-bfgs-b',
                          jac=obj_func_jac,
                          tol=tolerance,
                          options={'disp':True,
                                   'maxls':20})

    return Coordinate(basis, *min_result.x[-3:])
