# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import autograd.numpy as np

import scipy

from calipy import math, calib

from autograd import elementwise_grad

def PCM_obj_func(x, args):

    M = args['M']
    m = args['m']
    delta = args['delta']

    num_all_res = args['num_feats'] * args['num_frames'] * args['num_cameras']

    x_use = PCM_x_usable(x, args)

    # multi
    obj_func_val_x = PCM_calc_res_x(x_use[:, 0], x_use[:, 1], x_use[:, 2],
                               x_use[:, 3], x_use[:, 4], x_use[:, 5],
                               x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                               x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                               x_use[:, 15], x_use[:, 16], x_use[:, 17],
                               x_use[:, 18], x_use[:, 19], x_use[:, 20],
                               M, m, delta,
                               num_all_res)
    obj_func_val_y = PCM_calc_res_y(x_use[:, 0], x_use[:, 1], x_use[:, 2],
                               x_use[:, 3], x_use[:, 4], x_use[:, 5],
                               x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                               x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                               x_use[:, 15], x_use[:, 16], x_use[:, 17],
                               x_use[:, 18], x_use[:, 19], x_use[:, 20],
                               M, m, delta,
                               num_all_res)

    obj_func_val = np.concatenate([obj_func_val_x, obj_func_val_y], 0)

    return obj_func_val


def PCM_calc_res_x(rX1_0, rX1_1, rX1_2,
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
    x_ = x_pre * (1 + (k_1 * r2) + (k_2 * r2**2) + (k_3 * r2**3)) + \
        (2 * p_1 * x_pre * y_pre) + \
        (p_2 * (r2 + 2 * x_pre**2))
    # A * m_proj
    x_post = (x_ * fx) + cx

    res_x = delta * (x_post - m[:, 0])

    return res_x

def PCM_calc_res_y(rX1_0, rX1_1, rX1_2,
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
    y_ = y_pre * (1 + (k_1 * r2) + (k_2 * r2**2) + (k_3 * r2**3)) + \
        (p_1 * (r2 + 2 * y_pre**2)) + \
        (2 * p_2 * x_pre * y_pre)
    # A * m_proj
    y_post = (y_ * fy) + cy

    res_y = delta * (y_post - m[:, 1])

    return res_y

def PCM_unwrap_x(x, args):

    num_cameras = args['num_cameras']
    num_frames = args['num_frames']
    refcam_idx = args['refcam_idx']

    A_size = args['A_size']
    d_size = args['d_size']
    d_flags = args['d_flags']
    d_true_size = args['d_true_size']
    r_size = args['r_size']
    t_size = args['t_size']

    idx = 0
    # rX1
    rX1_ref = np.zeros((1, 3))
    rX1_others = x[idx:idx + (r_size * (num_cameras - 1))].reshape((num_cameras - 1), r_size)
    rX1 = np.concatenate([rX1_others[:refcam_idx, :], rX1_ref, rX1_others[refcam_idx:, :]], 0)
    idx += r_size * (num_cameras - 1)
    # tX1
    tX1_ref = np.zeros((1, 3))
    tX1_others = x[idx:idx + (t_size * (num_cameras - 1))].reshape((num_cameras - 1), t_size)
    tX1 = np.concatenate([tX1_others[:refcam_idx, :], tX1_ref, tX1_others[refcam_idx:, :]], 0)
    idx += t_size * (num_cameras - 1)
    # A
    A = x[idx:idx + (A_size * num_cameras)].reshape(num_cameras, A_size)
    idx += A_size * num_cameras
    # d
    d = np.zeros(d_size * num_cameras)
    d[np.resize(d_flags, d_size * num_cameras)] = x[idx:idx + (d_true_size * num_cameras)]
    d = d.reshape(num_cameras, d_size)
    idx += d_true_size * num_cameras
    # r1
    r1 = x[idx:idx + (r_size * num_frames)].reshape(num_frames, r_size)
    idx += r_size * num_frames
    # t1
    t1 = x[idx:idx + (t_size * num_frames)].reshape(num_frames, t_size)

    return rX1, tX1, A, d, r1, t1

def PCM_x_usable(x, args):

    num_cameras = args['num_cameras']
    num_frames = args['num_frames']
    num_feats = args['num_feats']
    num_all_res = args['num_feats'] * args['num_frames'] * args['num_cameras']

    A_size = args['A_size']
    d_size = args['d_size']
    r_size = args['r_size']
    t_size = args['t_size']

    num_frame_vars = args['num_frame_vars']
    num_all_vars = args['num_all_vars']

    # multi
    x_use = np.zeros((num_all_res, num_frame_vars), dtype=float)

    rX1, tX1, A, d, r1, t1 = PCM_unwrap_x(x, args)

    res_idx = 0
    for cam_idx in range(num_cameras):

        rX1_others = np.repeat(rX1[cam_idx].reshape(1, r_size), num_feats, axis=0)
        tX1_others = np.repeat(tX1[cam_idx].reshape(1, t_size), num_feats, axis=0)
        A_others = np.repeat(A[cam_idx].reshape(1, A_size), num_feats, axis=0)
        d_others = np.repeat(d[cam_idx].reshape(1, d_size), num_feats, axis=0)


        for frame_idx in range(num_frames):
            res_idx1 = res_idx * num_feats
            res_idx += 1
            res_idx2 = res_idx * num_feats
            i = 0
            # rX1
            x_use[res_idx1 : res_idx2, i : i + r_size] = rX1_others
            i = i + r_size
            # tX1
            x_use[res_idx1 : res_idx2, i : i + t_size] = tX1_others
            i = i + t_size
            # A
            x_use[res_idx1 : res_idx2, i : i + A_size] = A_others
            i = i + A_size
            # d
            x_use[res_idx1 : res_idx2, i : i + d_size] = d_others
            i = i + d_size
            # r1
            r1_others = np.repeat(r1[frame_idx].reshape(1, r_size), num_feats, axis=0)
            x_use[res_idx1 : res_idx2, i : i + r_size] = r1_others
            i = i + r_size
            # t1
            t1_others = np.repeat(t1[frame_idx].reshape(1, t_size), num_feats, axis=0)
            x_use[res_idx1 : res_idx2, i : i + t_size] = t1_others


    return x_use

def PCM_obj_func_jac(x, args):
    num_cameras = args['num_cameras']
    num_frames = args['num_frames']
    num_feats = args['num_feats']
    num_all_res = args['num_feats'] * args['num_frames'] * args['num_cameras']
    num_all_vars = args['num_all_vars']

    A_size = args['A_size']
    #d_size = args['d_size']
    #d_flags = args['d_flags']
    d_true_size = args['d_true_size']
    r_size = args['r_size']
    t_size = args['t_size']

    refcam_idx = args['refcam_idx']

    #
    x_use = PCM_x_usable(x, args)

    M = args['M']
    m = args['m']
    delta = args['delta']

    num_res_per_cam = num_frames * num_feats
    obj_func_jac_val_x = np.zeros((num_all_res, num_all_vars), dtype=np.float64)
    obj_func_jac_val_y = np.zeros((num_all_res, num_all_vars), dtype=np.float64)

    # MULTI
    args_idx = 0
    out_idx = 0
    index_ref = np.ones(num_all_res, dtype=bool)
    index_ref1 = refcam_idx * num_res_per_cam
    index_ref2 = (refcam_idx + 1) * num_res_per_cam
    index_ref[index_ref1:index_ref2] = False

    # rX1
    for i in range(0, r_size, 1):

        df_dx = args['jac_x'][i + args_idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                          x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                          x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8], x_use[index_ref, 9],
                                          x_use[index_ref, 10], x_use[index_ref, 11], x_use[index_ref, 12], x_use[index_ref, 13], x_use[index_ref, 14],
                                          x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                          x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                          M[index_ref], m[index_ref], delta[index_ref],
                                          num_all_res-num_res_per_cam).reshape(num_cameras - 1, num_res_per_cam)

        obj_func_jac_val_x[index_ref, i + out_idx:r_size * (num_cameras - 1) + out_idx:r_size] = scipy.linalg.block_diag(*df_dx).T

        df_dx = args['jac_y'][i + args_idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                          x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                          x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8], x_use[index_ref, 9],
                                          x_use[index_ref, 10], x_use[index_ref, 11], x_use[index_ref, 12], x_use[index_ref, 13], x_use[index_ref, 14],
                                          x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                          x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                          M[index_ref], m[index_ref], delta[index_ref],
                                          num_all_res-num_res_per_cam).reshape(num_cameras - 1, num_res_per_cam)

        obj_func_jac_val_y[index_ref, i + out_idx:r_size * (num_cameras - 1) + out_idx:r_size] = scipy.linalg.block_diag(*df_dx).T

    args_idx += r_size
    out_idx += (num_cameras - 1) * r_size

    # tX1
    for i in range(0, t_size, 1):
        df_dx = args['jac_x'][i + args_idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                          x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                          x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8], x_use[index_ref, 9], x_use[index_ref, 10],
                                          x_use[index_ref, 11], x_use[index_ref, 12], x_use[index_ref, 13], x_use[index_ref, 14],
                                          x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                          x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                          M[index_ref], m[index_ref], delta[index_ref],
                                          num_all_res-num_res_per_cam).reshape(num_cameras - 1, num_res_per_cam)

        obj_func_jac_val_x[index_ref, i + out_idx:t_size * (num_cameras - 1) + out_idx:t_size] = scipy.linalg.block_diag(*df_dx).T
        df_dx = args['jac_y'][i + args_idx](x_use[index_ref, 0], x_use[index_ref, 1], x_use[index_ref, 2],
                                          x_use[index_ref, 3], x_use[index_ref, 4], x_use[index_ref, 5],
                                          x_use[index_ref, 6], x_use[index_ref, 7], x_use[index_ref, 8], x_use[index_ref, 9], x_use[index_ref, 10],
                                          x_use[index_ref, 11], x_use[index_ref, 12], x_use[index_ref, 13], x_use[index_ref, 14],
                                          x_use[index_ref, 15], x_use[index_ref, 16], x_use[index_ref, 17],
                                          x_use[index_ref, 18], x_use[index_ref, 19], x_use[index_ref, 20],
                                          M[index_ref], m[index_ref], delta[index_ref],
                                          num_all_res-num_res_per_cam).reshape(num_cameras - 1, num_res_per_cam)

        obj_func_jac_val_y[index_ref, i + out_idx:t_size * (num_cameras - 1) + out_idx:t_size] = scipy.linalg.block_diag(*df_dx).T
    args_idx += t_size
    out_idx += (num_cameras - 1) * t_size

    # A
    A_size_use = int(A_size / 2)
    for i in range(0, A_size_use, 1):
        df_dx = args['jac_x'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res).reshape(num_cameras, num_res_per_cam)

        obj_func_jac_val_x[:, i + out_idx:A_size * num_cameras + out_idx:A_size] = scipy.linalg.block_diag(*df_dx).T

        df_dx = args['jac_y'][i + A_size_use + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res).reshape(num_cameras, num_res_per_cam)

        obj_func_jac_val_y[:, i + A_size_use + out_idx:A_size * num_cameras + out_idx:A_size] = scipy.linalg.block_diag(*df_dx).T

    args_idx += A_size
    out_idx += num_cameras * A_size

    # d
    for i in range(0, d_true_size, 1):
        df_dx = args['jac_x'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res).reshape(num_cameras, num_res_per_cam)

        obj_func_jac_val_x[:, i + out_idx:d_true_size * num_cameras + out_idx:d_true_size] = scipy.linalg.block_diag(*df_dx).T

        df_dx = args['jac_y'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res).reshape(num_cameras, num_res_per_cam)

        obj_func_jac_val_y[:, i + out_idx:d_true_size * num_cameras + out_idx:d_true_size] = scipy.linalg.block_diag(*df_dx).T

    args_idx += d_true_size
    out_idx += num_cameras * d_true_size


    index_local = np.ones((num_frames, num_feats), dtype=bool)
    index_global_sub = scipy.linalg.block_diag(*index_local).T
    index_global = np.tile(index_global_sub, (num_cameras, 1))

    # r1
    for i in range(0, r_size, 1):
        df_dx = args['jac_x'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res)

        obj_func_jac_val_x[:, i + out_idx:r_size * num_frames + out_idx:r_size][index_global] = df_dx

        df_dx = args['jac_y'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res)

        obj_func_jac_val_y[:, i + out_idx:r_size * num_frames + out_idx:r_size][index_global] = df_dx

    args_idx += r_size
    out_idx += num_frames * r_size

    # t1
    for i in range(0, t_size, 1):
        df_dx = args['jac_x'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res)

        obj_func_jac_val_x[:, i + out_idx:t_size * num_frames + out_idx:t_size][index_global] = df_dx
        df_dx = args['jac_y'][i + args_idx](x_use[:, 0], x_use[:, 1], x_use[:, 2],
                                          x_use[:, 3], x_use[:, 4], x_use[:, 5],
                                          x_use[:, 6], x_use[:, 7], x_use[:, 8], x_use[:, 9],
                                          x_use[:, 10], x_use[:, 11], x_use[:, 12], x_use[:, 13], x_use[:, 14],
                                          x_use[:, 15], x_use[:, 16], x_use[:, 17],
                                          x_use[:, 18], x_use[:, 19], x_use[:, 20],
                                          M, m, delta,
                                          num_all_res)

        obj_func_jac_val_y[:, i + out_idx:t_size * num_frames + out_idx:t_size][index_global] = df_dx


    obj_func_jac_val = np.concatenate([obj_func_jac_val_x, obj_func_jac_val_y], 0)

    return obj_func_jac_val