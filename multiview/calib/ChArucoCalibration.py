# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

import numpy as np

import cv2


class ChArucoCalibration:

    def __init__(self, context):
        self.context = context

        self.name = "ChAruco Calibration"

        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_100)

        self.board_size = (5, 7)
        self.marker_size = (1, 0.6)

        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)

        self.params = cv2.aruco.DetectorParameters_create()
        self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    def detect(self, frame):
        detected = {}

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
        result = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

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

    def calibrate_camera(self, size, detected, calibration):
        # Ignore ill-defined boards
        min_count = max(min(self.board.getChessboardSize()), 10)

        corners = [d['square_corners'] for d in detected if 'square_corners' in d and len(d['square_corners']) >= min_count]
        ids = [d['square_ids'] for d in detected if 'square_ids' in d and len(d['square_ids']) >= min_count]
        rej = [index for index, d in enumerate(detected) if 'square_ids' not in d or len(d['square_ids']) < min_count]

        print("In ({}) - Rej ({}) = {}".format(len(detected), len(rej), len(corners)))

        # Disable p1, p2, k2 and k3 distortion coefficients
        flags = cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3
        critia = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 1e-3)

        P = None
        d = None

        if calibration is not None:
            P = calibration['P']
            d = calibration['d']
            flags |= cv2.CALIB_USE_INTRINSIC_GUESS

        err, P, d, Rs, ts = cv2.aruco.calibrateCameraCharuco(corners, ids, self.board, size, P, d, None, None, flags, critia)

        return {'err': err, 'P': P, 'd': d, 'Rs': Rs, 'ts': ts, 'rej': rej}
