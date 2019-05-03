# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import cv2


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

        self.params = cv2.aruco.DetectorParameters_create()
        self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    def configure(self, parameters):
        self.board_size = (parameters['square_x'][0], parameters['square_y'][0])
        self.marker_size = (parameters['square_length'][0], parameters['marker_length'][0])

        dictionary_id = { 4: cv2.aruco.DICT_4X4_1000,
                          5: cv2.aruco.DICT_5X5_1000,
                          6: cv2.aruco.DICT_6X6_1000,
                          7: cv2.aruco.DICT_7X7_1000}[parameters['dictionary'][0]]

        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)

    def detect(self, frame):
        detected = {}

        if frame.ndim > 2 and frame.shape[2] > 1:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Find Aruco markers in image
        marker_corners, marker_ids, rejected = cv2.aruco.detectMarkers(frame, self.dictionary, None, None, self.params)

        marker_corners, marker_ids, _, _ = cv2.aruco.refineDetectedMarkers(frame, self.board, marker_corners, marker_ids, rejected)

        if marker_corners:
            detected["marker_corners"] = marker_corners
            detected["marker_ids"] = marker_ids

            # Find Aruco checkerboard in image
            result, square_corners, square_ids = cv2.aruco.interpolateCornersCharuco(marker_corners, marker_ids, frame, self.board)

            if square_corners is not None:
                detected["square_corners"] = square_corners
                detected["square_ids"] = square_ids

        return detected

    def extract(self, detection):
        if 'square_corners' not in detection:
            return None

        img_pts = detection['square_corners']
        obj_pts = self.board.chessboardCorners[detection['square_ids']]

        return {'obj_pts': obj_pts, 'img_pts':  img_pts}

    def draw(self, frame, detected):

        if 'marker_corners' in detected:
            cv2.aruco.drawDetectedMarkers(frame, detected['marker_corners'])

        if 'square_corners' in detected:
            cv2.aruco.drawDetectedCornersCharuco(frame, detected['square_corners'])

        return frame
