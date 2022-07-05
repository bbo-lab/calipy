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


class PinholeCameraModel:
    ID = "opencv-pinhole"
    NAME = "Pinhole Camera"

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

        corners_nn = corners_cam[mask]
        corners_use, ids_use = calib.corners_array_to_ragged(corners_nn)

        cal_res = cv2.aruco.calibrateCameraCharucoExtended(corners_use,  # noqa
                                                           ids_use,
                                                           board.make_board(board_params),
                                                           sensor_size,
                                                           None,
                                                           None,
                                                           **opts['detection']['aruco_calibration'])

        rvecs = np.empty(shape=(mask.size, 3))
        rvecs[:] = np.NaN
        tvecs = np.empty(shape=(mask.size, 3))
        tvecs[:] = np.NaN
        retval, A, k, = cal_res[0:3]

        rvecs[mask, :] = np.asarray(cal_res[3])[..., 0]
        tvecs[mask, :] = np.asarray(cal_res[4])[..., 0]

        cal = {
            'rvec_cam': np.asarray([0., 0., 0.]),
            'tvec_cam': np.asarray([0., 0., 0.]),
            'A': np.asarray(A),
            'k': np.asarray(k),
            'rvecs': np.asarray(rvecs),
            'tvecs': np.asarray(tvecs),
            'repro_error': retval,
            # Not that from here on values are NOT expanded to full frames range, see frames_mask
            'std_intrinsics': cal_res[5],
            'std_extrinsics': cal_res[6],
            'per_view_errors': cal_res[7],
            'frames_mask': mask,
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

        calibs_multi = pose_estimation.estimate_cam_poses(calibs_single, calibrator_opts.get_default_opts(), corners=corners,
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
        pose_opts['free_vars']['A'][:] = False
        pose_opts['free_vars']['k'][:] = False

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

        calibs_fit, rvecs_boards, tvecs_boards, min_result, args = \
            self.optimize_calib_parameters(corners, calibs_multi, board_params,
                                                   [(0, 0) for _ in range(corners.shape[0])],
                                                   opts=opts)

        residuals_objfun = np.abs(optimization.obj_fcn_wrapper(min_result.x, args).reshape(corners.shape))
        residuals_objfun[residuals_objfun == 0] = np.NaN

        return calibs_fit, rvecs_boards, tvecs_boards, min_result, residuals_objfun, args

    @staticmethod
    def optimize_calib_parameters(corners, calibs_multi, board_params, offsets, opts=None):
        if opts is None:
            opts = {}
        defaultopts = calibrator_opts.get_default_opts()
        opts = helper.deepmerge_dicts(opts, defaultopts)

        start_time = timeit.default_timer()

        board_coords_3d_0 = board.make_board_points(board_params)

        # Generate vectors of all and of free variables
        vars_free, vars_full, mask_free_input = optimization.make_initialization(calibs_multi, corners, board_params,
                                                                                 offsets, opts)

        args = {
            'vars_full': vars_full,  # All possible vars, free vars will be substituted in _free wrapper functions
            'mask_opt': mask_free_input,  # Mask of free vars within all vars
            'opts_free_vars': opts['free_vars'],
            'coord_cam': opts['coord_cam'],  # This is currently only required due to unsolved jacobian issue
            'board_coords_3d_0': board_coords_3d_0,  # Board points in z plane
            'corners': corners,
            'precalc': optimization.get_precalc(),
            # Inapplicable tue to autograd slice limitations
            # 'memory': {  # References to memory that can be reused, avoiding cost of reallocation
            #     'residuals': np.zeros_like(corners),
            #     'boards_coords_3d': np.zeros_like(boards_coords_3d_0),
            #     'boards_coords_3d_cams': np.zeros_like(boards_coords_3d_0),
            #     'calibs': calibs_fit,
            # }
        }

        # This triggers JIT compilation
        optimization.obj_fcn_wrapper(vars_free, args)
        # This times
        tic = timeit.default_timer()
        result = optimization.obj_fcn_wrapper(vars_free, args)
        print(
            f"Objective function took {timeit.default_timer() - tic} s: squaresum {np.sum(result ** 2)} over {result.size} residuals.")

        if opts['numerical_jacobian']:
            jac = '2-point'
        else:
            jac = optimization.obj_fcn_jacobian_wrapper
            # This triggers JIT compilation
            jac(vars_free, args)
            # This times
            tic = timeit.default_timer()
            result = jac(vars_free, args)
            print(
                f"Jacobian took {timeit.default_timer() - tic} s: squaresum {np.sum(result ** 2)} over {result.size} residuals.")

        # Check quality of calibration, tested working (requires calibcamlib >=0.2.3 on path)
        camfunctions.test_objective_function(calibs_multi, vars_free, args, corners, board_params, offsets)

        print('Starting optimization procedure')
        # TODO Test if alternating optimization between camera parameters and poses with a breaking critierion on camera
        #  params could be more efficient ... I think often cam params are optimal quite quickly and the opimization runs on
        #  some rougue poses ...
        min_result: OptimizeResult = least_squares(optimization.obj_fcn_wrapper,
                                                   vars_free,
                                                   jac=jac,
                                                   bounds=np.array([[-np.inf, np.inf]] * vars_free.size).T,
                                                   args=[args],
                                                   **opts['optimization'])

        current_time = timeit.default_timer()
        print('Optimization algorithm converged:\t{:s}'.format(str(min_result.success)))
        print('Time needed:\t\t\t\t{:.0f} seconds'.format(current_time - start_time))

        calibs_fit, rvecs_boards, tvecs_boards = optimization.unravel_to_calibs(min_result.x, args)

        # We don't include poses in the calibs_fit dictionary, as the final calibration structure should be independent
        #  of the calibration process
        calibs_test = [
            {**calibs_fit[i_cam], **{
                'rvecs': rvecs_boards,
                'tvecs': tvecs_boards}
             }
            for i_cam in range(len(calibs_fit))
        ]
        camfunctions.test_objective_function(calibs_test, min_result.x, args, corners, board_params, offsets, individual_poses=True)

        return calibs_fit, rvecs_boards, tvecs_boards, min_result, args

    def draw(self, frame, detected, calibration, estimation):

        if calibration and estimation and ('square_ids' in detected):
            if 'rvec' in estimation:
                rvec = (R.from_rotvec(calibration['rvec_cam']) *
                        R.from_rotvec(estimation['rvec'])).as_rotvec().reshape((-1, 3))
                tvec = R.from_rotvec(calibration['rvec_cam']).apply(estimation['tvec']) + calibration['tvec_cam']
            else:
                rvec = (R.from_rotvec(calibration['rvec_cam']) *
                        R.from_rotvec(estimation['rvec_board'])).as_rotvec().reshape((-1, 3))
                tvec = R.from_rotvec(calibration['rvec_cam']).apply(estimation['tvec_board']) + calibration['tvec_cam']

            cv2.aruco.drawAxis(frame, calibration['A'], calibration['k'], rvec, tvec, 10.0)

            obj_points = self.board.chessboardCorners[detected['square_ids']]

            if len(obj_points):
                img_points, _ = cv2.projectPoints(obj_points, rvec, tvec, calibration['A'],
                                                  calibration['k'])

                for point in img_points:
                    cv2.drawMarker(frame, (point[0][0], point[0][1]), (255, 0, 255))

        return frame
