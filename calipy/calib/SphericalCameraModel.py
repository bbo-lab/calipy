# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1


import cv2

import autograd.numpy as np

from calipy import calib

from joblib import Parallel, delayed

import multiprocessing

from calibcam import board, pose_estimation, calibrator_opts

from calibcam import camfunctions, helper, optimization

import timeit

from copy import deepcopy

from scipy.optimize import least_squares, OptimizeResult

from scipy.spatial.transform import Rotation as R  # noqa


class SphericalCameraModel:
    ID = "opencv-omnidir"
    NAME = "Spherical Camera"

    def __init__(self, context):
        self.context = context

        self.dictionary_id = 6
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_100)

        self.board_size = (5, 7)
        self.marker_size = (1, 0.6)

        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)
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
        self.board = cv2.aruco.CharucoBoard_create(*self.board_size, *self.marker_size, self.dictionary)
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

    def perform_single_cam_calibrations(self, corners_all, ids_all, sizes, frames_masks):
        print('PERFORM SINGLE CAMERA CALIBRATION')

        corners = calib.make_corners_array(corners_all, ids_all, self.num_feats, frames_masks)
        num_cams = frames_masks.shape[0]

        print(int(np.floor(multiprocessing.cpu_count())))

        # Board params in the format used in Calibcam
        board_params = self.board_params_calibcam()

        calibs_single = Parallel(n_jobs=int(np.floor(multiprocessing.cpu_count())))(
            delayed(self.calibrate_single_camera)(corners[i_cam],
                                                  sizes[i_cam],
                                                  board_params,
                                                  calibrator_opts.get_default_opts())
            for i_cam in range(num_cams))

        for i_cam, calib_cam in enumerate(calibs_single):
            print(
                f'Used {(~np.isnan(calib_cam["rvecs"][:, 1])).sum(dtype=int):03d} '
                f'frames for single cam calibration for cam {i_cam:02d}'
            )
            print(calib_cam['rvecs'][0])
            print(calib_cam['tvecs'][0])

        return calibs_single

    @staticmethod
    def calibrate_single_camera(corners_cam, sensor_size, board_params, opts, mask=None):
        if mask is None:
            mask = np.sum(~np.isnan(corners_cam[:, :, 1]),
                          axis=1) > 0  # Test for degeneration should be performed beforehand and respective frames excluded from corner array

        n_used_frames = np.sum(mask)

        if n_used_frames == 0:
            return []

        object_points_cam = np.zeros((*corners_cam.shape[0:2], 3))
        object_points_cam[:] = board.make_board_points(board_params)

        corners_nn = corners_cam[mask]
        mask_2 = np.isnan(corners_nn[:, :, 1])
        object_points_nn = object_points_cam[mask]
        object_points_nn[mask_2] = np.nan

        corners_use, _ = calib.corners_array_to_ragged(corners_nn)
        object_points_use, _ = calib.corners_array_to_ragged(object_points_nn)

        cal_res = cv2.omnidir.calibrate(object_points_use,  # noqa
                                        corners_use,
                                        sensor_size,
                                        None,
                                        None,
                                        None,
                                        **opts['detection']['aruco_calibration'])

        mask_final = np.zeros_like(mask, dtype=bool)
        mask_final[np.where(mask)[0][cal_res[6].flatten()]] = True

        rvecs = np.empty(shape=(mask_final.size, 3))
        rvecs[:] = np.NaN
        tvecs = np.empty(shape=(mask_final.size, 3))
        tvecs[:] = np.NaN
        retval, K, xi, D = cal_res[0:4]

        rvecs[mask_final, :] = np.asarray(cal_res[4])[..., 0]
        tvecs[mask_final, :] = np.asarray(cal_res[5])[..., 0]

        cal = {
            'rvec_cam': np.asarray([0., 0., 0.]),
            'tvec_cam': np.asarray([0., 0., 0.]),
            'K': np.asarray(K),
            'xi': np.asarray(xi),
            'D': np.asarray(D),
            'rvecs': np.asarray(rvecs),
            'tvecs': np.asarray(tvecs),
            'repro_error': retval,
            # Not that from here on values are NOT expanded to full frames range, see frames_mask
            'idx': cal_res[6],
            'frames_mask': mask_final,
        }
        print('Finished single camera calibration.')
        return cal

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
