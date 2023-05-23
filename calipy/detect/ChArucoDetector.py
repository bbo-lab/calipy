# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import cv2

from collections import OrderedDict

import math

import numpy as np


class ChArucoDetector:
    ID = "charuco"
    NAME = "ChAruco Pattern"
    PARAMS = [
        {'name': 'square_x', 'title': 'Board Width', 'type': 'int', 'value': 10},
        {'name': 'square_y', 'title': 'Board Height', 'type': 'int', 'value': 10},
        {'name': 'square_length', 'title': 'Square Length (m)', 'type': 'float', 'value': 0.1016},
        {'name': 'marker_length', 'title': 'Marker Length (m)', 'type': 'float', 'value': 0.0762},
        {'name': 'dictionary', 'title': 'Marker Resolution', 'type': 'list', 'value': 4, 'values': [4, 5, 6, 7]}
    ]

    def __init__(self, context):
        self.context = context

        self.dictionary = None
        self.board_size = (10, 10)
        self.marker_size = (0.1016, 0.0762)
        self.board = None

        self.num_feats = (self.board_size[0] - 1) * (self.board_size[1] - 1)
        self.min_det_feats = int(max(self.board_size))

        self.params = cv2.aruco.DetectorParameters_create()
        self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    def configure(self, board_params):
        self.board_size = (board_params['square_x'][0], board_params['square_y'][0])
        self.PARAMS[0]['value'] = board_params['square_x'][0]
        self.PARAMS[1]['value'] = board_params['square_y'][0]

        self.marker_size = (board_params['square_length'][0], board_params['marker_length'][0])
        self.PARAMS[2]['value'] = board_params['square_length'][0]
        self.PARAMS[3]['value'] = board_params['marker_length'][0]

        dictionary_id = {4: cv2.aruco.DICT_4X4_1000,
                         5: cv2.aruco.DICT_5X5_1000,
                         6: cv2.aruco.DICT_6X6_1000,
                         7: cv2.aruco.DICT_7X7_1000}[board_params['dictionary'][0]]

        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)

        self.num_feats = (self.board_size[0] - 1) * (self.board_size[1] - 1)
        self.min_det_feats = int(max(self.board_size))

    @staticmethod
    def board_params_calipy(calibcam_npy):

        # TODO: correct the dictionary thing
        if 'board_coords_3d_0' in calibcam_npy['info']['other']:
            num_object_pts = calibcam_npy['info']['other']['board_coords_3d_0'].shape[0] + 1
        else:
            num_object_pts = 36
        board_params_calibcam = calibcam_npy['board_params']

        return OrderedDict([('square_x', (board_params_calibcam['boardWidth'], OrderedDict())),
                            ('square_y', (board_params_calibcam['boardHeight'], OrderedDict())),
                            ('square_length', (board_params_calibcam['square_size_real'], OrderedDict())),
                            ('marker_length', (board_params_calibcam['marker_size_real'], OrderedDict())),
                            ('dictionary', (int(math.sqrt(num_object_pts)), OrderedDict()))
                            ])

    @staticmethod
    def extract_calibcam(corners_array):
        square_ids = np.where(~np.isnan(np.sum(corners_array, axis=1)))[0]

        square_corners = corners_array[square_ids]

        return {'square_ids': square_ids.reshape(-1, 1),
                'square_corners': square_corners.reshape(-1, 1, 2)}

    def extract(self, detection):
        if 'square_corners' not in detection:
            return None

        image_pts = detection['square_corners']
        square_ids = detection['square_ids']
        object_pts = self.board.chessboardCorners[detection['square_ids']]

        return {'object_pts': object_pts, 'image_pts': image_pts, 'square_ids': square_ids}

    @staticmethod
    def draw(frame, detected):

        if 'marker_corners' in detected:
            cv2.aruco.drawDetectedMarkers(frame, detected['marker_corners'])

        if 'square_corners' in detected:
            cv2.aruco.drawDetectedCornersCharuco(frame, detected['square_corners'])

        return frame
