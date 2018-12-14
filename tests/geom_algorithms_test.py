import unittest

import multiview.geom as mvg

import numpy as np

class GeomAlgorithmTests(unittest.TestCase):
    def test_coord_from_image_point(self):
        # Load camera system
        basis, cams = mvg.CameraSystem.fromCalNpz("tests/data/test.cal.npz")

        # Load image points
        points = np.load("tests/data/test.pts.npy");

        # Load expected coords
        coords = basis.coordsFromNpyFile("tests/data/test.coord.npy")

        for pt, coord in zip(points, coords):
            pt_objs = [c.newImagePoint(*pt[i, :]) for i, c in enumerate(cams)]

            estimate = mvg.findCoordinateFromImagePoints(pt_objs)

            self.assertAlmostEqual(estimate.x, coord.x)
            self.assertAlmostEqual(estimate.y, coord.y)
            self.assertAlmostEqual(estimate.z, coord.z)

    def test_coord_to_image_point_to_coord(self):
        # Load test camera system
        basis, cams_sys = mvg.CameraSystem.fromCalNpz("tests/data/test.cal.npz")

        # Ground truth point
        coord_gt = basis.newCoordinate(202, -500, 2193)

        # Project point into cameras
        image_points = [c.project(coord_gt) for c in cams_sys]

        # Compute 3D coordinate
        coord_comp = mvg.findCoordinateFromImagePoints(image_points)

        # Test reprojection
        self.assertAlmostEqual(coord_gt.x, coord_comp.x)
        self.assertAlmostEqual(coord_gt.y, coord_comp.y)
        self.assertAlmostEqual(coord_gt.z, coord_comp.z)

    def test_basis_ridgid_body_align(self):
        # Create transform
        R = mvg.rodrigues2matrix(np.random.randn(3))
        t = np.random.randint(100) * np.random.randn(3)

        trans = mvg.RidgidBodyTransform(R, t)

        # Generate random coords
        basis = mvg.Basis()
        X = np.random.rand(100, 3)
        coords_basis = basis.coordsFromMatrix(X)

        # Transform †hem to other basis
        other = mvg.Basis()
        Y = trans.apply(X)
        coords_other = other.coordsFromMatrix(Y)

        # Find similarity transform
        mvg.findRidgidBodyTransform(coords_basis, coords_other)
        trans_est = basis.getTransform(other)

        # Check result
        np.testing.assert_array_almost_equal(trans.R, trans_est.R)
        np.testing.assert_array_almost_equal(trans.t, trans_est.t)

    def test_basis_similarity_align(self):
        # Create transform
        s = abs(np.random.randint(100) * np.random.randn())
        R = mvg.rodrigues2matrix(np.random.randn(3))
        t = np.random.randint(100) * np.random.randn(3)

        trans = mvg.SimilarityTransform(s, R, t)

        # Generate random coords
        basis = mvg.Basis()
        X = np.random.rand(100, 3)
        coords_basis = basis.coordsFromMatrix(X)

        # Transform †hem to other basis
        other = mvg.Basis()
        Y = trans.apply(X)
        coords_other = other.coordsFromMatrix(Y)

        # Find similarity transform
        mvg.findSimilarityTransform(coords_basis, coords_other)
        trans_est = basis.getTransform(other)

        # Check result
        self.assertAlmostEqual(trans.s, trans_est.s)
        np.testing.assert_array_almost_equal(trans.R, trans_est.R)
        np.testing.assert_array_almost_equal(trans.t, trans_est.t)
