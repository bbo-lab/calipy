# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

import cv2


class ChArucoDetector:
    ID = "ChAruco"
    NAME = "ChAruco Pattern"

    def __init__(self, context):
        self.context = context

        if False:
            self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_100)

            self.board_size = (5, 7)
            self.marker_size = (1, 0.6)
        else:
            self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)

            self.board_size = (10, 10)
            self.marker_size = (1, 0.75)

        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)

        self.params = cv2.aruco.DetectorParameters_create()
        self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

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

    def draw(self, frame, detected, calibration, estimation):
        if frame.ndim < 3 or frame.shape[2] == 1:
            result = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            result = frame.copy()

        if 'marker_corners' in detected:
            cv2.aruco.drawDetectedMarkers(result, detected['marker_corners'])

        if 'square_corners' in detected:
            cv2.aruco.drawDetectedCornersCharuco(result, detected['square_corners'])

        if calibration and estimation:
            cv2.aruco.drawAxis(result, calibration['P'], calibration['d'], estimation['R'], estimation['t'], 1.0)

            obj_points = self.board.chessboardCorners[detected['square_ids']]

            img_points, _ = cv2.projectPoints(obj_points, estimation['R'], estimation['t'], calibration['P'], calibration['d'])

            for point in img_points:
                cv2.drawMarker(result, (point[0][0], point[0][1]), (255, 0, 255))

        return result
