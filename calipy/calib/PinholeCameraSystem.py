import autograd.numpy as np

import scipy

from calipy import calib

from autograd import elementwise_grad


class PinholeCameraSystem:
    ID = "custom-pinhole-system"
    NAME = "Pinhole Camera System"

    def __init__(self, model: object, d_flags: np.ndarray, num_cameras: int, refcam_idx: int, num_frames: int):

        self.model = model

        self.A_size = 4
        self.A_use_idx = np.array([True, False, True,
                                   False, True, True,
                                   False, False, False], dtype=bool)
        self.d_size = 5
        self.d_flags = d_flags
        self.d_true_size = int(np.sum(d_flags))
        self.r_size = 3
        self.t_size = 3

        self.num_cameras = num_cameras
        self.num_frames = num_frames

        self.num_frame_vars = self.r_size + self.t_size + \
                              self.A_size + self.d_size + \
                              self.r_size + self.t_size
        self.num_true_frame_vars = self.r_size + self.t_size + \
                                   self.A_size + self.d_true_size + \
                                   self.r_size + self.t_size
        self.num_all_vars = (num_cameras - 1) * (self.r_size + self.t_size) + \
                            num_cameras * self.d_true_size + \
                            num_cameras * self.A_size + \
                            num_frames * (self.r_size + self.t_size)

        self.refcam_idx = refcam_idx

        self.jac_x = None
        self.jac_y = None

        self.M = None
        self.m = None
        self.delta = None

    def obj_func(self, x):

        num_all_res = self.model.num_feats * self.num_frames * self.num_cameras

        x_use = self.x_usable(x)

        obj_func_val_x = self.calc_res_x(x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res)
        obj_func_val_y = self.calc_res_y(x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res)

        obj_func_val = np.concatenate([obj_func_val_x, obj_func_val_y], 0)

        return obj_func_val

    @staticmethod
    def calc_res_x(rX1_0, rX1_1, rX1_2,
                   tX1_0, tX1_1, tX1_2,
                   fx, cx, fy, cy,
                   k_1, k_2, p_1, p_2, k_3,
                   r1_0, r1_1, r1_2,
                   t1_0, t1_1, t1_2,
                   M, m, delta,
                   num_all_res):
        x_pre, y_pre, r2 = calib.map_m(rX1_0, rX1_1, rX1_2,
                                       tX1_0, tX1_1, tX1_2,
                                       r1_0, r1_1, r1_2,
                                       t1_0, t1_1, t1_2,
                                       M,
                                       num_all_res)
        # distort
        x_ = x_pre * (1 + (k_1 * r2) + (k_2 * r2 ** 2) + (k_3 * r2 ** 3)) + \
             (2 * p_1 * x_pre * y_pre) + \
             (p_2 * (r2 + 2 * x_pre ** 2))
        # A * m_proj
        x_post = (x_ * fx) + cx

        res_x = delta * (x_post - m[:, 0])

        return res_x

    @staticmethod
    def calc_res_y(rX1_0, rX1_1, rX1_2,
                   tX1_0, tX1_1, tX1_2,
                   fx, cx, fy, cy,
                   k_1, k_2, p_1, p_2, k_3,
                   r1_0, r1_1, r1_2,
                   t1_0, t1_1, t1_2,
                   M, m, delta,
                   num_all_res):
        x_pre, y_pre, r2 = calib.map_m(rX1_0, rX1_1, rX1_2,
                                       tX1_0, tX1_1, tX1_2,
                                       r1_0, r1_1, r1_2,
                                       t1_0, t1_1, t1_2,
                                       M,
                                       num_all_res)
        # distort
        y_ = y_pre * (1 + (k_1 * r2) + (k_2 * r2 ** 2) + (k_3 * r2 ** 3)) + \
             (p_1 * (r2 + 2 * y_pre ** 2)) + \
             (2 * p_2 * x_pre * y_pre)
        # A * m_proj
        y_post = (y_ * fy) + cy

        res_y = delta * (y_post - m[:, 1])

        return res_y

    def unwrap_x(self, x):

        idx = 0
        # rX1
        rX1_ref = np.zeros((1, 3))
        rX1_others = x[idx:idx + (self.r_size * (self.num_cameras - 1))].reshape((self.num_cameras - 1), self.r_size)
        rX1 = np.concatenate([rX1_others[:self.refcam_idx, :], rX1_ref, rX1_others[self.refcam_idx:, :]], 0)
        idx += self.r_size * (self.num_cameras - 1)
        # tX1
        tX1_ref = np.zeros((1, 3))
        tX1_others = x[idx:idx + (self.t_size * (self.num_cameras - 1))].reshape((self.num_cameras - 1), self.t_size)
        tX1 = np.concatenate([tX1_others[:self.refcam_idx, :], tX1_ref, tX1_others[self.refcam_idx:, :]], 0)
        idx += self.t_size * (self.num_cameras - 1)
        # A
        A = x[idx:idx + (self.A_size * self.num_cameras)].reshape(self.num_cameras, self.A_size)
        idx += self.A_size * self.num_cameras
        # d
        d = np.zeros(self.d_size * self.num_cameras)
        d[np.resize(self.d_flags, self.d_size * self.num_cameras)] = x[idx:idx + (self.d_true_size * self.num_cameras)]
        d = d.reshape(self.num_cameras, self.d_size)
        idx += self.d_true_size * self.num_cameras
        # r1
        r1 = x[idx:idx + (self.r_size * self.num_frames)].reshape(self.num_frames, self.r_size)
        idx += self.r_size * self.num_frames
        # t1
        t1 = x[idx:idx + (self.t_size * self.num_frames)].reshape(self.num_frames, self.t_size)

        return rX1, tX1, A, d, r1, t1

    def x_usable(self, x):

        num_all_res = self.model.num_feats * self.num_frames * self.num_cameras

        # multi
        x_use = np.zeros((num_all_res, self.num_frame_vars), dtype=float)

        rX1, tX1, A, d, r1, t1 = self.unwrap_x(x)

        res_idx = 0
        for cam_idx in range(self.num_cameras):

            rX1_others = np.repeat(rX1[cam_idx].reshape(1, self.r_size), self.model.num_feats, axis=0)
            tX1_others = np.repeat(tX1[cam_idx].reshape(1, self.t_size), self.model.num_feats, axis=0)
            A_others = np.repeat(A[cam_idx].reshape(1, self.A_size), self.model.num_feats, axis=0)
            d_others = np.repeat(d[cam_idx].reshape(1, self.d_size), self.model.num_feats, axis=0)

            for frame_idx in range(self.num_frames):
                res_idx1 = res_idx * self.model.num_feats
                res_idx += 1
                res_idx2 = res_idx * self.model.num_feats
                i = 0
                # rX1
                x_use[res_idx1: res_idx2, i: i + self.r_size] = rX1_others
                i = i + self.r_size
                # tX1
                x_use[res_idx1: res_idx2, i: i + self.t_size] = tX1_others
                i = i + self.t_size
                # A
                x_use[res_idx1: res_idx2, i: i + self.A_size] = A_others
                i = i + self.A_size
                # d
                x_use[res_idx1: res_idx2, i: i + self.d_size] = d_others
                i = i + self.d_size
                # r1
                r1_others = np.repeat(r1[frame_idx].reshape(1, self.r_size), self.model.num_feats, axis=0)
                x_use[res_idx1: res_idx2, i: i + self.r_size] = r1_others
                i = i + self.r_size
                # t1
                t1_others = np.repeat(t1[frame_idx].reshape(1, self.t_size), self.model.num_feats, axis=0)
                x_use[res_idx1: res_idx2, i: i + self.t_size] = t1_others

        return x_use

    def define_jacobian(self):
        self.jac_x = np.zeros(self.num_true_frame_vars, dtype=object)
        self.jac_y = np.zeros(self.num_true_frame_vars, dtype=object)
        index = 0
        for var_idx in range(self.r_size + self.t_size + self.A_size):
            self.jac_x[var_idx] = elementwise_grad(self.calc_res_x, var_idx)
            self.jac_y[var_idx] = elementwise_grad(self.calc_res_y, var_idx)
        index += (self.r_size + self.t_size + self.A_size)

        index2 = 0
        for var_idx in range(index, index + self.d_size):
            if self.d_flags[var_idx - index]:
                self.jac_x[index + index2] = elementwise_grad(self.calc_res_x, var_idx)
                self.jac_y[index + index2] = elementwise_grad(self.calc_res_y, var_idx)
                index2 += 1
        index3 = index + self.d_true_size
        index += self.d_size

        for var_idx in range(self.r_size + self.t_size):
            self.jac_x[index3 + var_idx] = elementwise_grad(self.calc_res_x, index + var_idx)
            self.jac_y[index3 + var_idx] = elementwise_grad(self.calc_res_y, index + var_idx)

    def obj_func_jac(self, x):

        num_all_res = self.model.num_feats * self.num_frames * self.num_cameras

        x_use = self.x_usable(x)

        num_res_per_cam = self.num_frames * self.model.num_feats
        obj_func_jac_val_x = np.zeros((num_all_res, self.num_all_vars), dtype=np.float64)
        obj_func_jac_val_y = np.zeros((num_all_res, self.num_all_vars), dtype=np.float64)

        # MULTI
        _idx = 0
        out_idx = 0
        index_ref = np.ones(num_all_res, dtype=bool)
        index_ref1 = self.refcam_idx * num_res_per_cam
        index_ref2 = (self.refcam_idx + 1) * num_res_per_cam
        index_ref[index_ref1:index_ref2] = False

        # rX1
        for i in range(0, self.r_size, 1):
            df_dx = self.jac_x[i + _idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                         x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                         x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8],
                                         x_use[index_ref, 9],
                                         x_use[index_ref, 10], x_use[index_ref, 11], x_use[index_ref, 12],
                                         x_use[index_ref, 13], x_use[index_ref, 14],
                                         x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                         x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                         self.M[index_ref], self.m[index_ref], self.delta[index_ref],
                                         num_all_res - num_res_per_cam).reshape(self.num_cameras - 1, num_res_per_cam)

            obj_func_jac_val_x[index_ref, i + out_idx:self.r_size * (self.num_cameras - 1) + out_idx:self.r_size] = \
                scipy.linalg.block_diag(*df_dx).T

            df_dx = self.jac_y[i + _idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                         x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                         x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8],
                                         x_use[index_ref, 9],
                                         x_use[index_ref, 10], x_use[index_ref, 11], x_use[index_ref, 12],
                                         x_use[index_ref, 13], x_use[index_ref, 14],
                                         x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                         x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                         self.M[index_ref], self.m[index_ref], self.delta[index_ref],
                                         num_all_res - num_res_per_cam).reshape(self.num_cameras - 1, num_res_per_cam)

            obj_func_jac_val_y[index_ref, i + out_idx:self.r_size * (self.num_cameras - 1) + out_idx:self.r_size] = \
                scipy.linalg.block_diag(*df_dx).T

        _idx += self.r_size
        out_idx += (self.num_cameras - 1) * self.r_size

        # tX1
        for i in range(0, self.t_size, 1):
            df_dx = self.jac_x[i + _idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                         x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                         x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8],
                                         x_use[index_ref, 9], x_use[index_ref, 10],
                                         x_use[index_ref, 11], x_use[index_ref, 12], x_use[index_ref, 13],
                                         x_use[index_ref, 14],
                                         x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                         x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                         self.M[index_ref], self.m[index_ref], self.delta[index_ref],
                                         num_all_res - num_res_per_cam).reshape(self.num_cameras - 1, num_res_per_cam)

            obj_func_jac_val_x[index_ref, i + out_idx:self.t_size * (self.num_cameras - 1) + out_idx:self.t_size] = \
                scipy.linalg.block_diag(*df_dx).T
            df_dx = self.jac_y[i + _idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                         x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                         x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8],
                                         x_use[index_ref, 9], x_use[index_ref, 10],
                                         x_use[index_ref, 11], x_use[index_ref, 12], x_use[index_ref, 13],
                                         x_use[index_ref, 14],
                                         x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                         x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                         self.M[index_ref], self.m[index_ref], self.delta[index_ref],
                                         num_all_res - num_res_per_cam).reshape(self.num_cameras - 1, num_res_per_cam)

            obj_func_jac_val_y[index_ref, i + out_idx:self.t_size * (self.num_cameras - 1) + out_idx:self.t_size] = \
                scipy.linalg.block_diag(*df_dx).T

        _idx += self.t_size
        out_idx += (self.num_cameras - 1) * self.t_size

        # A
        A_size_use = int(self.A_size / 2)
        for i in range(0, A_size_use, 1):
            df_dx = self.jac_x[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res).reshape(self.num_cameras, num_res_per_cam)

            obj_func_jac_val_x[:, i + out_idx:self.A_size * self.num_cameras + out_idx:self.A_size] = \
                scipy.linalg.block_diag(*df_dx).T

            df_dx = self.jac_y[i + A_size_use + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                                      x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                                      x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                                      x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13],
                                                      x_use[:, 14],
                                                      x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                                      x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                                      self.M, self.m, self.delta,
                                                      num_all_res).reshape(self.num_cameras, num_res_per_cam)

            obj_func_jac_val_y[:, i + A_size_use + out_idx:self.A_size * self.num_cameras + out_idx:self.A_size] = \
                scipy.linalg.block_diag(*df_dx).T

        _idx += self.A_size
        out_idx += self.num_cameras * self.A_size

        # d
        for i in range(0, self.d_true_size, 1):
            df_dx = self.jac_x[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res).reshape(self.num_cameras, num_res_per_cam)

            obj_func_jac_val_x[:, i + out_idx:self.d_true_size * self.num_cameras + out_idx:self.d_true_size] = \
                scipy.linalg.block_diag(*df_dx).T

            df_dx = self.jac_y[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res).reshape(self.num_cameras, num_res_per_cam)

            obj_func_jac_val_y[:, i + out_idx:self.d_true_size * self.num_cameras + out_idx:self.d_true_size] = \
                scipy.linalg.block_diag(*df_dx).T

        _idx += self.d_true_size
        out_idx += self.num_cameras * self.d_true_size

        index_local = np.ones((self.num_frames, self.model.num_feats), dtype=bool)
        index_global_sub = scipy.linalg.block_diag(*index_local).T
        index_global = np.tile(index_global_sub, (self.num_cameras, 1))

        # r1
        for i in range(0, self.r_size, 1):
            df_dx = self.jac_x[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res)

            obj_func_jac_val_x[:, i + out_idx:self.r_size * self.num_frames + out_idx:self.r_size][index_global] = df_dx

            df_dx = self.jac_y[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res)

            obj_func_jac_val_y[:, i + out_idx:self.r_size * self.num_frames + out_idx:self.r_size][index_global] = df_dx

        _idx += self.r_size
        out_idx += self.num_frames * self.r_size

        # t1
        for i in range(0, self.t_size, 1):
            df_dx = self.jac_x[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res)

            obj_func_jac_val_x[:, i + out_idx:self.t_size * self.num_frames + out_idx:self.t_size][index_global] = df_dx
            df_dx = self.jac_y[i + _idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                         x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                         x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                         x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                         x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                         x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                         self.M, self.m, self.delta,
                                         num_all_res)

            obj_func_jac_val_y[:, i + out_idx:self.t_size * self.num_frames + out_idx:self.t_size][index_global] = df_dx

        obj_func_jac_val = np.concatenate([obj_func_jac_val_x, obj_func_jac_val_y], 0)

        return obj_func_jac_val
