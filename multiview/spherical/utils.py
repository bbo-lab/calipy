import numpy as np

def longlatSphericalAxis(width, height, radius=None):
    """
    Return grid axis for long-lat spherical image representation.

    0 < inclination < pi
    0 < azimuth < 2 pi

    radius is ignored by default, but can be set via optional radius flag.
    """

    (inclination, step) = np.linspace(0, np.pi, height, endpoint=False, retstep=True)
    inclination += step/2

    (azimuth, step) = np.linspace(0, 2 * np.pi, width, endpoint=False, retstep=True)
    azimuth += step/2

    if radius is None:
        return inclination, azimuth
    else:
        return radius, inclination, azimuth


def longlatSphericalGrid(width, height, radius=None):
    """
    Return grid for long-lat spherical image representation.

    radius is ignored by default, but can be set via optional radius flag.
    """

    return tuple(np.meshgrid(*longlatSphericalAxis(width, height, radius)))


def longlatCartesianGrid(width, height):
    """
    Return cartesian grid for long-lat sperical image representation.

    radius is assumed to be one.
    """

    inclination, azimuth = longlatSphericalAxis(width, height)

    cartesian = np.zeros([height, width, 3])

    sin_inc = np.sin(inclination)
    cos_inc = np.cos(inclination)
    sin_azi = np.sin(azimuth)
    cos_azi = np.cos(azimuth)

    for u in range(width):
        for v in range(height):
            cartesian[v, u, 0] = sin_inc[v] * cos_azi[u]
            cartesian[v, u, 1] = sin_inc[v] * sin_azi[u]
            cartesian[v, u, 2] = cos_inc[v]

    return cartesian

