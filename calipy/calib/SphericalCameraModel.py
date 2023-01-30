# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1


import cv2

import numpy as np

from calipy import calib

from calipy.calib import utils

from joblib import Parallel, delayed

import multiprocessing

from calibcam import board, pose_estimation, calibrator_opts

from calibcam import camfunctions, helper, optimization

from calibcamlib import Camera

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

        corners = utils.make_corners_array(corners_all, ids_all, self.num_feats, frames_masks)
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

        # TODO: shift this to an apt position
        opts['detection']['aruco_calibration']['flags'] = 0
        print(opts['detection']['aruco_calibration'])

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
            # Note that from here on values are NOT expanded to full frames range, see frames_mask
            'idx': cal_res[6],
            'frames_mask': mask_final,
        }
        print('Finished single camera calibration.')
        return cal

    def perform_multi_calibration(self, calibs_single, corners_all, ids_all, frames_masks):

        corners = calib.make_corners_array(corners_all, ids_all, self.num_feats, frames_masks)

        required_corner_idxs = [0,
                                self.board_size[0] - 1,
                                (self.board_size[0] - 1) * (self.board_size[1] - 2),
                                (self.board_size[0] - 1) * (self.board_size[1] - 1) - 1,
                                ]

        calibs_multi = pose_estimation.estimate_cam_poses(calibs_single, calibrator_opts.get_default_opts(),
                                                          corners=corners,
                                                          required_corner_idxs=required_corner_idxs)

        print('OPTIMIZING POSES')

        # self.plot(calibs_single, corners, used_frames_ids, self.board_params, 3, 35)

        calibs_fit, rvecs_boards, tvecs_boards, min_result, args = self.optimize_poses(corners, calibs_multi)
        calibs_fit = helper.combine_calib_with_board_params(calibs_fit, rvecs_boards, tvecs_boards)

        print('OPTIMIZING ALL PARAMETERS')

        return self.optimize_calibration(corners, calibs_fit)

    def optimize_poses(self, corners, calibs_multi, opts=None, board_params=None):
        if opts is None:
            opts = calibrator_opts.get_default_opts()
        if board_params is None:
            # Board params in the format used in Calibcam
            board_params = self.board_params_calibcam()

        pose_opts = deepcopy(opts)

        # Modify the pose_opts for OpenCv omnidirectional camera
        pose_opts['free_vars'] = {'cam_pose': True,
                                  'board_poses': True,
                                  'K': np.asarray(
                                      [[False, False, False],  # a   c   u   (c is skew and should not be necessary)
                                       [False, False, False],  # 0   b   v
                                       [False, False, False],  # 0   0   1
                                       ]),
                                  'D': np.zeros(5),
                                  'xi': False  # 1: optimize, 0: leave const, -1: force 0
                                  }

        calibs_fit, rvecs_boards, tvecs_boards, min_result, args = \
            self.optimize_calib_parameters(corners, calibs_multi, board_params,
                                           [(0, 0) for _ in range(corners.shape[0])],
                                           opts=pose_opts)

        return calibs_fit, rvecs_boards, tvecs_boards, min_result, args

    def optimize_calibration(self, corners, calibs_multi, opts=None, board_params=None):
        if opts is None:
            opts = calibrator_opts.get_default_opts()
        if board_params is None:
            # Board params in the format used in Calibcam
            board_params = self.board_params_calibcam()

        pose_opts = deepcopy(opts)
        # Modify the pose_opts for OpenCv omnidirectional camera
        pose_opts['free_vars'] = {'cam_pose': True,
                                  'board_poses': True,
                                  'K': np.asarray(
                                      [[True, False, True],  # a   c   u   (c is skew and should not be necessary)
                                       [False, True, True],  # 0   b   v
                                       [False, False, False],  # 0   0   1
                                       ]),
                                  'D': np.asarray([1, 1, -1, -1]),
                                  'xi': True  # 1: optimize, 0: leave const, -1: force 0
                                  }

        calibs_fit, rvecs_boards, tvecs_boards, min_result, args = \
            self.optimize_calib_parameters(corners, calibs_multi, board_params,
                                           [(0, 0) for _ in range(corners.shape[0])],
                                           opts=pose_opts)

        residuals_objfun = np.abs(optimization.obj_fcn_wrapper(min_result.x, args).reshape(corners.shape))
        residuals_objfun[residuals_objfun == 0] = np.NaN

        return calibs_fit, rvecs_boards, tvecs_boards, min_result, residuals_objfun, args

    def draw(self, frame, detected, calibration, estimation):

        if calibration and estimation and ('square_ids' in detected):
            if 'rvec' in estimation:
                rmat = (R.from_rotvec(calibration['rvec_cam']) *
                        R.from_rotvec(estimation['rvec'])).as_matrix()
                tvec = R.from_rotvec(calibration['rvec_cam']).apply(estimation['tvec']) + calibration['tvec_cam']
            else:
                rmat = (R.from_rotvec(calibration['rvec_cam']) *
                        R.from_rotvec(estimation['rvec_board'])).as_matrix()
                tvec = R.from_rotvec(calibration['rvec_cam']).apply(estimation['tvec_board']) + calibration['tvec_cam']

            obj_points = self.board.chessboardCorners[detected['square_ids']]

            if len(obj_points):
                obj_points = np.squeeze(obj_points)
                coords_cam = (rmat @ obj_points.T).T + tvec.reshape(1, 3)
                cam = Camera(calibration['K' if 'K' in calibration else 'A'],
                             calibration['D' if 'D' in calibration else 'k'],
                             xi=calibration['xi'][0])
                img_points_2 = cam.space_to_sensor(coords_cam).T.T

                for point in img_points_2:
                    cv2.drawMarker(frame, (int(point[0]), int(point[1])), (0, 0, 255))

        return frame
