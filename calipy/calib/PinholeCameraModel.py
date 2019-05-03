# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import cv2


class PinholeCameraModel:
    ID = "opencv-pinhole"
    NAME = "Pinhole Camera"

    def __init__(self, context):
        self.context = context

        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_100)

        self.board_size = (5, 7)
        self.marker_size = (1, 0.6)

        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)

    def calibrate_camera(self, size, object_points, image_points, calibration):
        # Disable p1, p2, k2 and k3 distortion coefficients
        flags = cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3
        critia = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 20, 0.0001)

        P = None
        d = None

        if calibration is not None:
            P = calibration['P']
            d = calibration['d']
            flags |= cv2.CALIB_USE_INTRINSIC_GUESS

        err, P, d, Rs, ts = cv2.calibrateCamera(object_points, image_points, size, P, d, None, None, flags, critia)

        return {'err': err, 'P': P, 'd': d, 'Rs': Rs, 'ts': ts}

    def calibrate_system(self, *kwargs):
        raise NotImplementedError("Pinhole system calibration not implemented yet")

    def draw(self, frame, detected, calibration, estimation):

        if calibration and estimation:
            cv2.aruco.drawAxis(frame, calibration['P'], calibration['d'], estimation['R'], estimation['t'], 1.0)

            obj_points = self.board.chessboardCorners[detected['square_ids']]

            img_points, _ = cv2.projectPoints(obj_points, estimation['R'], estimation['t'], calibration['P'], calibration['d'])

            for point in img_points:
                cv2.drawMarker(frame, (point[0][0], point[0][1]), (255, 0, 255))

        return frame
