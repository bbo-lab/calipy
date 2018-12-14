import unittest

import multiview.geom as mvg

import numpy as np

class GeomRebaseTests(unittest.TestCase):
    def test_circluar(self):
        # Load camera system
        basis, cams = mvg.CameraSystem.fromCalNpz("tests/data/test.cal.npz")

        # Load expected coords
        coords = basis.coordsFromNpyFile("tests/data/test.coord.npy")

        coords_rebased = [p.rebase(cams[0], basis).rebase(cams[1], basis).rebase(cams[2], basis).rebase(cams[3], basis).rebase(basis) for p in coords]

        assert(coords[0].basis is coords_rebased[0].basis)

        for c1, c2 in zip(coords, coords_rebased):
            self.assertAlmostEqual(c1.x, c2.x)
            self.assertAlmostEqual(c1.y, c2.y)
            self.assertAlmostEqual(c1.z, c2.z)

    def test_projection_origin(self):
        basis = mvg.Basis()

        R = mvg.rodrigues2matrix(np.random.randn(3))
        t = np.random.randint(100) * np.random.randn(3)

        a = 2000 * np.random.rand(4)
        A = np.array([[a[0],    0, a[1]],
                      [   0, a[2], a[3]],
                      [   0,    0,    1]])

        proj = mvg.Projection(basis, R, t, A)

        coord_to = proj.toCoordinate(proj.basis)

        coord_rebase = proj.newCoordinate(0, 0, 0).rebase(proj.basis)

        self.assertAlmostEqual(coord_to.x, coord_rebase.x)
        self.assertAlmostEqual(coord_to.y, coord_rebase.y)
        self.assertAlmostEqual(coord_to.z, coord_rebase.z)
