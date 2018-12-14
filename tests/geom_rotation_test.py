import unittest

import multiview.geom as mvg

import numpy as np

class GeomRotationTests(unittest.TestCase):
    def test_rot_quat_to_mat_to_quat(self):
        q1 = np.array([0.06335886, -0.41029575, -0.88180592,  0.223744])

        M = mvg.Rotation.fromQuaternions(*q1).toMatrix()

        q2 = mvg.Rotation.fromMatrix(M).toQuaternions()

        for i in range(4):
            self.assertAlmostEqual(q1[i], q2[i])
