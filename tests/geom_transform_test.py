import unittest

import multiview.geom as mvg

import numpy as np

class GeomTransformTests(unittest.TestCase):
    def test_rigid_inv(self):
        R = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t = np.random.randint(100) * np.random.randn(3)

        X = np.random.rand(25, 3)

        transform = mvg.RidgidBodyTransform(R, t)

        X_trans = transform.invert().apply(transform.apply(X))

        np.testing.assert_array_almost_equal(X, X_trans)

    def test_rigid_fog(self):
        R_f = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t_f = np.random.randint(100) * np.random.randn(3)

        f = mvg.RidgidBodyTransform(R_f, t_f)

        R_g = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t_g = np.random.randint(100) * np.random.randn(3)

        g = mvg.RidgidBodyTransform(R_g, t_g)

        X = np.random.rand(25, 3)

        Y_chain = f.apply(g.apply(X))

        Y_fog = (f @ g).apply(X)

        np.testing.assert_array_almost_equal(Y_chain, Y_fog)

    def test_simil_fog(self):
        s_f = 10 * np.random.randn()
        R_f = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t_f = np.random.randint(100) * np.random.randn(3)

        f = mvg.SimilarityTransform(s_f, R_f, t_f)

        s_g = 10 * np.random.randn()
        R_g = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t_g = np.random.randint(100) * np.random.randn(3)

        g = mvg.SimilarityTransform(s_g, R_g, t_g)

        X = np.random.rand(25, 3)

        Y_chain = f.apply(g.apply(X))

        Y_fog = (f @ g).apply(X)

        np.testing.assert_array_almost_equal(Y_chain, Y_fog)

    def test_simil_inv(self):
        s = 10 * np.random.randn()
        R = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t = np.random.randint(100) * np.random.randn(3)

        X = np.random.rand(25, 3)

        transform = mvg.SimilarityTransform(s, R, t)

        X_trans = transform.invert().apply(transform.apply(X))

        np.testing.assert_array_almost_equal(X, X_trans)


    def test_mix_fog(self):
        R_f = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t_f = np.random.randint(100) * np.random.randn(3)

        f = mvg.RidgidBodyTransform(R_f, t_f)

        s_g = 10 * np.random.randn()
        R_g = mvg.Rotation.fromQuaternions(*np.random.randn(4)).toMatrix()[0:3,0:3]
        t_g = np.random.randint(100) * np.random.randn(3)

        g = mvg.SimilarityTransform(s_g, R_g, t_g)

        X = np.random.rand(25, 3)

        Y_chain = f.apply(g.apply(X))

        Y_fog = (f @ g).apply(X)

        np.testing.assert_array_almost_equal(Y_chain, Y_fog)

        Y_invchain = g.apply(f.apply(X))

        Y_gof = (g @ f).apply(X)

        np.testing.assert_array_almost_equal(Y_invchain, Y_gof)
