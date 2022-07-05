# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import enum

import numpy as np


class HSplitDirection(enum.IntEnum):
    Left = 0
    Right = 1


class HSplitFilter:
    """ Filter that only keeps left or right side of a frame. """
    def __init__(self, direction):
        self.direction = direction

    def apply(self, frame):
        # ToDo: Benchmark! Probably slow!
        return np.hsplit(frame, 2)[self.direction].copy()


FILTERS = {
    'HSplitLeft': HSplitFilter(HSplitDirection.Left),
    'HSplitRight': HSplitFilter(HSplitDirection.Right)
}
