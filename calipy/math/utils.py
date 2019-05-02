# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import numpy as np


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
