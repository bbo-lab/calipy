# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import cv2


class SphericalCameraModel:
    ID = "opencv-omnidir"
    NAME = "Spherical Camera"

    def __init__(self, context):
        self.context = context

        # FIXME: REMOVE!
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_100)

        self.board_size = (5, 7)
        self.marker_size = (1, 0.6)

        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)
        self.num_feats = (self.board_size[0] - 1) * (self.board_size[1] - 1)
        self.min_det_feats = int(max(self.board_size))

    def configure(self, parameters):
        self.board_size = (parameters['square_x'][0], parameters['square_y'][0])
        self.marker_size = (parameters['square_length'][0], parameters['marker_length'][0])

        dictionary_id = {4: cv2.aruco.DICT_4X4_1000,
                         5: cv2.aruco.DICT_5X5_1000,
                         6: cv2.aruco.DICT_6X6_1000,
                         7: cv2.aruco.DICT_7X7_1000}[parameters['dictionary'][0]]

        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)
        self.num_feats = (self.board_size[0] - 1) * (self.board_size[1] - 1)
        self.min_det_feats = int(max(self.board_size))

    @staticmethod
    def calibrate_camera(size, object_points, image_points, calibration):
        # Run calibration
        critia = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 500, 0.0001)
        flags = 0

        K = None
        xi = None
        D = None

        if calibration is not None:
            K = calibration['K']
            xi = calibration['xi']
            D = calibration['D']
            flags |= cv2.omnidir.CALIB_USE_GUESS

        err, K, xi, D, rvecs, tvecs, idx = cv2.omnidir.calibrate(object_points, image_points, size, K, xi, D, flags,
                                                                   critia)

        # TODO: Remove later

        return {'err': err, 'K': K, 'xi': xi, 'D': D, 'rvecs': rvecs, 'tvecs': tvecs, 'idx': idx}

    def calibrate_system(self, size, detections, calibrations):
        pass
        # Use intrinsic calibration
        # K1 = calibration[0]['K']
        # D1 = calibration[0]['D']
        # xi1 = calibration[0]['xi']
        #
        # K2 = calibration[1]['K']
        # D2 = calibration[1]['D']
        # xi2 = calibration[1]['xi']
        #
        # # Other settings
        # flags = cv2.CALIB_FIX_INTRINSIC
        # criteria = (cv2.TermCriteria_COUNT + cv2.TermCriteria_EPS, 200, 0.0001)
        #
        # size = (width // 2, height)
        #
        # # Collect data and object points
        # object_points = []
        # image_points1 = []
        # image_points2 = []
        #
        # for i in range(nframes):
        #
        #     # Check if both have detected features
        #     if np.all([detections[k][i]['ids_charuco'].size > 0 for k in range(2)]):
        #         shared = np.intersect1d(detections[0][i]['ids_charuco'],
        #                                 detections[1][i]['ids_charuco'])
        #
        #         # Skip frames with no shared feature for now
        #         if len(shared) < 3:
        #             continue
        #
        #         corners = board.chessboardCorners[shared]
        #
        #         # Make sure detected points are not all on one line
        #         if np.any(np.all(corners[:, :2] == corners[0, :2], axis=0)):
        #             continue
        #
        #         object_points.append(corners.reshape([-1, 1, 3]))
        #
        #         idx1 = np.equal(detections[0][i]['ids_charuco'], shared).any(axis=1)
        #         image_points1.append(detections[0][i]['corners_charuco'][idx1])
        #
        #         idx2 = np.equal(detections[1][i]['ids_charuco'], shared).any(axis=1)
        #         image_points2.append(detections[1][i]['corners_charuco'][idx2])
        #
        # n = len(object_points)
        # print("Running stereo calibration ...")
        # result_tuple = cv2.omnidir.stereoCalibrate(object_points,
        #                                            image_points1,
        #                                            image_points2,
        #                                            size,
        #                                            size,
        #                                            K1,
        #                                            xi1,
        #                                            D1,
        #                                            K2,
        #                                            xi2,
        #                                            D2,
        #                                            flags,
        #                                            criteria)
        #
        # rms_err, objP, imgP1, imgP, K1, xi1, D1, K2, xi2, D2, rvec, tvec, rvecsL, tvecsL, idx = result_tuple
        # print('    e = {}'.format(rms_err))

    def draw(self, frame, detected, calibration, estimation):

        if calibration and estimation:
            # TODO: Save used object point in estimation
            obj_points = self.board.chessboardCorners[detected['square_ids']]

            img_points, _ = cv2.omnidir.projectPoints(obj_points, estimation['rvec'], estimation['tvec'], calibration['K'], calibration['xi'], calibration['D'])

            for point in img_points:
                cv2.drawMarker(frame, (point[0][0], point[0][1]), (255, 0, 255))

        return frame
