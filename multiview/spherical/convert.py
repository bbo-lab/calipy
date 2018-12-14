from .utils import longlatSphericalGrid

import numpy as np

from scipy.interpolate import griddata

def spherical2longlat(spherical, values, width, height, radius=None):
    """
    Turn spherical pixels to long-lat image.

    spherical [nx3]
    values [n]

    Ignores radius by default, but can be set via optional flag
    """

    grid_sph = longlatSphericalGrid(width, height, radius)

    if radius is None:
        spherical = spherical[:, 1:3]

    return griddata(spherical, values, grid_sph).T


def cartesian2spherical(cartesian):
    """
    Turn cartesian to spherical coordinates

    cartesian [n x 3]
    """
    spherical = np.zeros_like(cartesian)

    for i, p in enumerate(cartesian):
        spherical[i, 0] = np.linalg.norm(p)
        spherical[i, 1] = np.arccos(p[2] / spherical[i, 0])
        spherical[i, 2] = np.arctan2(p[1], p[0]) % (2 * np.pi)

    return spherical
