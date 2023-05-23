# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import numpy as np

import cv2


def make_board(board_params):
    board = cv2.aruco.CharucoBoard_create(*board_params['board_size'],  # noqa
                                          *board_params['marker_size'],
                                          cv2.aruco.getPredefinedDictionary(  # noqa
                                              board_params['dictionary_id']))

    return board
