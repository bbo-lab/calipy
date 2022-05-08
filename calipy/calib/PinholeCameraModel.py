# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import cv2

import autograd.numpy as np

import time

from scipy.optimize import least_squares

from calipy import calib

from .PinholeCameraSystem import PinholeCameraSystem


# noinspection PyPep8Naming
class PinholeCameraModel:
    ID = "opencv-pinhole"
    NAME = "Pinhole Camera"

    def __init__(self, context):
        self.context = context

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
        # Disable p1, p2, k2 and k3 distortion coefficients
        flags = cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K3  # | cv2.CALIB_FIX_K2
        critia = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 20, 0.0001)

        A = None
        d = None

        if calibration is not None:
            A = calibration['A']
            d = calibration['d']
            flags |= cv2.CALIB_USE_INTRINSIC_GUESS

        err, A, d, r_vecs, t_vecs = cv2.calibrateCamera(object_points, image_points, size, A, d, None, None, flags,
                                                        critia)

        return {'err': err, 'A': A, 'd': d, 'r_vecs': r_vecs, 't_vecs': t_vecs}

    def calibrate_system(self, size, square_ids, image_points, estimations, calibrations, flags, system_calibration):

        num_cameras = len(square_ids)
        num_frames = len(square_ids[0])
        refcam_idx = system_calibration.get('refcam_idx', None)
        d_flags = np.array([1, 1, 0, 0, 0], dtype=bool)

        system = PinholeCameraSystem(self, d_flags, num_cameras, refcam_idx, num_frames)

        r_cam, t_cam = calib.calc_xcam(square_ids, estimations, system)

        # Define and initialise a single array containing all the parameters to be optimised
        x0 = np.zeros(system.num_all_vars, dtype=np.float64)

        i = 0
        # r_X1
        for cam_idx in range(num_cameras):
            if cam_idx != refcam_idx:
                r_X1 = r_cam['r_{:d}_{:d}'.format(cam_idx, refcam_idx)]
                x0[i:i + system.r_size] = r_X1.ravel()
                i += system.r_size
        # t_X1
        for cam_idx in range(num_cameras):
            if cam_idx != refcam_idx:
                t_X1 = t_cam['t_{:d}_{:d}'.format(cam_idx, refcam_idx)]
                x0[i:i + system.t_size] = t_X1.ravel()
                i += system.t_size
        # A
        A_use_idx = np.array([True, False, True,
                              False, True, True,
                              False, False, False], dtype=bool)
        for cam_idx in range(num_cameras):
            A = calibrations[cam_idx]['A']
            x0[i:i + system.A_size] = A.ravel()[A_use_idx]
            i += system.A_size
        # d
        for cam_idx in range(num_cameras):
            d = calibrations[cam_idx]['d']
            x0[i:i + system.d_true_size] = d.ravel()[d_flags]
            i += system.d_true_size
        # r_1
        for frame_idx in range(num_frames):
            r_1 = estimations[refcam_idx][frame_idx]['r_vec']
            x0[i:i + system.r_size] = r_1.ravel()
            i += system.r_size
        # t_1
        for frame_idx in range(num_frames):
            t_1 = estimations[refcam_idx][frame_idx]['t_vec']
            x0[i:i + system.t_size] = t_1.ravel()
            i += system.t_size

        rX1_0, tX1_0, A_0, d_0, r1_0, t1_0 = system.unwrap_x(x0)
        print(rX1_0, tX1_0, A_0, d_0)

        # Define object_points vector M and image_points vector m
        M, m, delta = calib.syscal_obtain_Mm(self.board_size, self.marker_size[0], square_ids, image_points, system)
        system.M = M
        system.m = m
        system.delta = delta

        # Define Jacobian
        print('\t - Defining jacobian')
        system.define_jacobian()

        # Define other optimization params
        bounds_ = np.array([[-np.inf, np.inf]] * np.size(x0)).T
        tol_ = np.finfo(np.float64).eps  # machine epsilon

        print('Starting optimization procedure - This might take a while')
        print('The following lines are associated with the current state of the optimization procedure:')
        start_time = time.time()

        min_result = least_squares(system.obj_func,
                                   x0,
                                   jac=system.obj_func_jac,
                                   bounds=bounds_,
                                   method='trf',
                                   ftol=tol_,
                                   xtol=tol_,
                                   gtol=tol_,
                                   x_scale='jac',
                                   loss='linear',
                                   tr_solver='exact',
                                   max_nfev=np.inf,
                                   verbose=2)

        current_time = time.time()
        print('Optimization algorithm converged:\t{:s}'.format(str(min_result.success)))
        print('Time needed:\t\t\t\t{:.0f} seconds'.format(current_time - start_time))
        system_calibration['message'] = min_result.message
        system_calibration['convergence'] = min_result.success

        if min_result.success:

            rX1_fit, tX1_fit, A_fit, d_fit, r1_fit, t1_fit = system.unwrap_x(min_result.x)

            for cam_idx in range(num_cameras):
                system_calibration['cam_{:d}'.format(cam_idx)] = {}
                system_calibration['cam_{:d}'.format(cam_idx)]['rX1'] = rX1_fit[cam_idx]
                system_calibration['cam_{:d}'.format(cam_idx)]['tX1'] = tX1_fit[cam_idx]
                system_calibration['cam_{:d}'.format(cam_idx)]['A'] = A_fit[cam_idx]
                system_calibration['cam_{:d}'.format(cam_idx)]['d'] = d_fit[cam_idx]

            system_calibration['refcam'] = {}
            for frm_idx in range(num_frames):
                system_calibration['refcam'][frm_idx] = {}
                system_calibration['refcam'][frm_idx]['r1'] = r1_fit[frm_idx]
                system_calibration['refcam'][frm_idx]['t1'] = t1_fit[frm_idx]

            num_all_res = int(min_result.fun.shape[0] / 2)
            residuals = np.vstack([min_result.fun[:num_all_res], min_result.fun[num_all_res:]]).T
            rms_error = np.sqrt(np.sum(np.square(residuals), axis=1))
            system_calibration['rms_error'] = rms_error
            system_calibration['mean_rms_error'] = np.sum(rms_error) / np.sum(delta)
            system_calibration['result'] = min_result

            print(rX1_fit, tX1_fit, A_fit, d_fit)

        return system_calibration

    def draw(self, frame, detected, calibration, estimation):

        if calibration and estimation:
            cv2.aruco.drawAxis(frame, calibration['A'], calibration['d'], estimation['r_vec'], estimation['t_vec'], 1.0)

            obj_points = self.board.chessboardCorners[detected['square_ids']]

            img_points, _ = cv2.projectPoints(obj_points, estimation['r_vec'], estimation['t_vec'], calibration['A'],
                                              calibration['d'])

            for point in img_points:
                cv2.drawMarker(frame, (point[0][0], point[0][1]), (255, 0, 255))

        return frame
