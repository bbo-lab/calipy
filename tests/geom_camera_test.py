import unittest

import multiview.geom as mvg

import numpy as np

class GeomCameraTests(unittest.TestCase):
    def test_distort_undistort(self):
        # Create camera with random params
        basis = mvg.Basis()

        R = np.eye(3)

        t = np.zeros(3)

        size = 1000
        f = size + size/2 * np.random.random()
        c = size/4 * (2 * np.random.random(2) - 1) + size/2
        A = np.array([[   f,   0, c[0]],
                      [   0,   f, c[1]],
                      [   0,   0,    1]])

        k = np.random.random(5) * 0.2 - 0.1

        cam = mvg.Camera(basis, R, t, A, k)

        # Create noisy grid of points across image plane
        points = []
        padding = 100
        for row in range(padding, size - padding, 5):
            for col in range(padding, size - padding, 5):
                points.append([row + (2 * np.random.random() - 1),
                               col + (2 * np.random.random() - 1)])

        points = np.array(points)

        # Test for each point
        for x, y in points:

            # undist of dist == id
            xd, yd = cam._distort(x, y)
            xu, yu = cam._undistort(xd, yd)

            self.assertAlmostEqual(x, xu, delta=1.0)
            self.assertAlmostEqual(y, yu, delta=1.0)

            # dist of undist == id
            xu, yu = cam._undistort(x, y)
            xd, yd = cam._distort(xu, yu)

            self.assertAlmostEqual(x, xd, delta=1.0)
            self.assertAlmostEqual(y, yd, delta=1.0)
