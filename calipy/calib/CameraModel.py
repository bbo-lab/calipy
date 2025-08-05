# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import calibcamlib
import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R  # noqa


class CameraModel:
    ID = "calibcam-camera"
    NAME = "Camera (Calibcam)"

    def __init__(self, context):
        self.context = context

        self.dictionary_id = 6
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_100)

        self.board_size = (5, 7)
        self.marker_size = (1, 0.6)

        self.board = cv2.aruco.CharucoBoard(self.board_size, *self.marker_size, self.dictionary)
        self.num_feats = (self.board_size[0] - 1) * (self.board_size[1] - 1)
        self.min_det_feats = int(max(self.board_size))

    def configure(self, parameters):
        self.board_size = (parameters['square_x'][0], parameters['square_y'][0])
        self.marker_size = (parameters['square_length'][0], parameters['marker_length'][0])

        self.dictionary_id = {4: cv2.aruco.DICT_4X4_1000,
                              5: cv2.aruco.DICT_5X5_1000,
                              6: cv2.aruco.DICT_6X6_1000,
                              7: cv2.aruco.DICT_7X7_1000}[parameters['dictionary'][0]]

        self.dictionary = cv2.aruco.getPredefinedDictionary(self.dictionary_id)
        self.board = cv2.aruco.CharucoBoard(self.board_size, *self.marker_size, self.dictionary)
        self.num_feats = (self.board_size[0] - 1) * (self.board_size[1] - 1)
        self.min_det_feats = int(max(self.board_size))

    def board_params_calibcam(self):
        return {'boardWidth': self.board_size[0],
                'boardHeight': self.board_size[1],
                'square_size_real': self.marker_size[0],
                'marker_size_real': self.marker_size[1],
                'square_size': 1.0,
                'marker_size': self.marker_size[1] / self.marker_size[0],
                'dictionary_type': self.dictionary_id}

    def draw(self, frame, detected, calibration, estimation):
        # TODO: clean it and switch to calibcamlib functions,
        if calibration and estimation and ('square_ids' in detected):
            if 'rvec' in estimation:
                rmat = (R.from_rotvec(calibration['rvec_cam']) *
                        R.from_rotvec(estimation['rvec'])).as_matrix()
                tvec = R.from_rotvec(calibration['rvec_cam']).apply(estimation['tvec']) + calibration['tvec_cam']
            else:
                rmat = (R.from_rotvec(calibration['rvec_cam']) *
                        R.from_rotvec(estimation['rvec_board'])).as_matrix()
                tvec = R.from_rotvec(calibration['rvec_cam']).apply(estimation['tvec_board']) + calibration['tvec_cam']

            obj_points = self.board.getChessboardCorners()[detected['square_ids']]

            if len(obj_points):
                obj_points = np.squeeze(obj_points)
                coords_cam = (rmat @ obj_points.T).T + tvec.reshape(1, 3)
                cam = calibcamlib.Camera(calibration['K' if 'K' in calibration else 'A'],
                                         calibration['D' if 'D' in calibration else 'k'],
                                         xi=calibration['xi'][0])
                img_points = cam.space_to_sensor(coords_cam).T.T

                for point in img_points:
                    cv2.drawMarker(frame, (int(point[0]), int(point[1])), (0, 0, 255))

        return frame


@DeprecationWarning
class PinholeCameraModel(CameraModel):
    ID = "opencv-pinhole"
    NAME = "Pinhole Camera"

    def __init__(self, context):
        super().__init__(context)


@DeprecationWarning
class SphericalCameraModel(CameraModel):
    ID = "opencv-omnidir"
    NAME = "Spherical Camera"

    def __init__(self, context):
        super().__init__(context)
