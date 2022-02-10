# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import autograd.numpy as np

from calipy import math

def calc_xcam(square_ids, estimations, args):

    # Calculate rotations and translations to translate from reference camera's coordinate system to other cameras coordiante systems
    # r - Rodrigues vector
    # R - Rotation matrix

    num_cameras = args['num_cameras']
    num_frames = args['num_frames']
    min_det_feats = args['min_det_feats']
    ref_cam_idx = args['ref_cam_idx']

    r_cam = {}
    t_cam = {}

    r11 = np.zeros((3, 1))
    r_cam['r_{:d}_{:d}'.format(ref_cam_idx, ref_cam_idx)] = r11
    t11 = np.zeros((3, 1))
    t_cam['t_{:d}_{:d}'.format(ref_cam_idx, ref_cam_idx)] = t11

    for cam_idx in range(num_cameras):

        if (cam_idx != ref_cam_idx):
            rX1 = np.zeros((3, 1), dtype = np.float64)
            RX1 = np.zeros((3, 3), dtype = np.float64)
            tX1 = np.zeros((3, 1), dtype = np.float64)
            num_frames_used = 0

            for frame_idx in range(num_frames):
                sq_ids_X = square_ids[cam_idx][frame_idx]
                sq_ids_1 = square_ids[ref_cam_idx][frame_idx]
                sq_ids_int = np.intersect1d(sq_ids_X, sq_ids_1)

                if (sq_ids_int.size >= min_det_feats):
                    # Calulating RX1, rotation matrix of camX, translates points from reference camera-cam1 coordinate system to that of camX
                    rot_vec_X = estimations[cam_idx][frame_idx]['r_vec'].ravel()
                    RX = math.rodrigues_2rotmat_single(rot_vec_X)
                    rot_vec_1 = estimations[ref_cam_idx][frame_idx]['r_vec'].ravel()
                    R1 = math.rodrigues_2rotmat_single(rot_vec_1)

                    RX1_add = np.dot(RX, R1.T)
                    RX1 += RX1_add

                    # Calulating tX1, translation vector of camX, translates points from reference camera-cam1 coordinate system to that of camX
                    tX = estimations[cam_idx][frame_idx]['t_vec']
                    t1 = estimations[ref_cam_idx][frame_idx]['t_vec']
                    tX1_add = (tX - np.dot(RX1_add, t1))
                    tX1 += tX1_add

                    num_frames_used += 1

            # Based on Curtis et al., A Note on Averaging Rotations (Lemma 2.2)
            u, s, vh = np.linalg.svd(RX1, full_matrices = True)
            RX1 = np.dot(u, vh)
            rX1 = math.rotmat_2rodrigues_single(RX1)
            r_cam['r_{:d}_{:d}'.format(cam_idx, ref_cam_idx)] = rX1
            tX1 = tX1 / num_frames_used
            t_cam['t_{:d}_{:d}'.format(cam_idx, ref_cam_idx)] = tX1
    return r_cam, t_cam

def syscal_obtain_Mm(board_size, square_length, square_ids, image_points, args):

    num_cameras = args['num_cameras']
    num_frames = args['num_frames']
    num_feats = args['num_feats']
    num_all_res = num_feats * num_frames * num_cameras
    board_width = board_size[0]
    board_height = board_size[1]

    # M
    M_0 = np.repeat(np.arange(1, board_width).reshape(1, board_width-1), board_height-1, axis=0).ravel().reshape(num_feats, 1)
    M_1 = np.repeat(np.arange(1, board_height), board_width-1, axis=0).reshape(num_feats, 1)
    M_ini = np.concatenate([M_0, M_1], 1)

    M = np.zeros((num_all_res, 2), dtype=np.float64)
    m = np.zeros((num_all_res, 2), dtype=np.float64)
    delta = np.zeros(num_all_res, dtype=np.float64)

    res_idx = 0
    for cam_idx in range(num_cameras):
        for frame_idx in range(num_frames):
            res_idx1 = res_idx * num_feats
            res_idx += 1
            res_idx2 = res_idx * num_feats

            # M
            # TODO: set object points
            M[res_idx1 : res_idx2 : 1] = M_ini * square_length

            img_pts = image_points[cam_idx][frame_idx]
            sq_ids = square_ids[cam_idx][frame_idx]
            if sq_ids.size:
                # m
                m[res_idx1 : res_idx2 : 1][sq_ids] = img_pts
                # delta
                delta[res_idx1 : res_idx2 : 1][sq_ids] = 1.0

    return M, m, delta


def map_m(rX1_0, rX1_1, rX1_2,
          tX1_0, tX1_1, tX1_2,
          r1_0, r1_1, r1_2,
          t1_0, t1_1, t1_2,
          M,
          num_all_res):
    # rX1
    rX1 = np.concatenate([rX1_0.reshape(num_all_res, 1),
                          rX1_1.reshape(num_all_res, 1),
                          rX1_2.reshape(num_all_res, 1)], 1)
    # tX1
    tX1 = np.concatenate([tX1_0.reshape(num_all_res, 1),
                          tX1_1.reshape(num_all_res, 1),
                          tX1_2.reshape(num_all_res, 1)], 1)
    # r1
    r1 = np.concatenate([r1_0.reshape(num_all_res, 1),
                         r1_1.reshape(num_all_res, 1),
                         r1_2.reshape(num_all_res, 1)], 1)
    # t1
    t1 = np.concatenate([t1_0.reshape(num_all_res, 1),
                         t1_1.reshape(num_all_res, 1),
                         t1_2.reshape(num_all_res, 1)], 1)


    RX1 = math.rodrigues_2rotmat(rX1)
    R1 = math.rodrigues_2rotmat(r1)

    # R1 * M + t1
    m_proj_0_1 = R1[:, 0, 0] * M[:, 0] + \
                 R1[:, 0, 1] * M[:, 1] + \
                 t1[:, 0]
    m_proj_1_1 = R1[:, 1, 0] * M[:, 0] + \
                 R1[:, 1, 1] * M[:, 1] + \
                 t1[:, 1]
    m_proj_2_1 = R1[:, 2, 0] * M[:, 0] + \
                 R1[:, 2, 1] * M[:, 1] + \
                 t1[:, 2]
    # RX1 * m_proj + tX1
    m_proj_0_2 = RX1[:, 0, 0] * m_proj_0_1 + \
                 RX1[:, 0, 1] * m_proj_1_1 + \
                 RX1[:, 0, 2] * m_proj_2_1 + \
                 tX1[:, 0]
    m_proj_1_2 = RX1[:, 1, 0] * m_proj_0_1 + \
                 RX1[:, 1, 1] * m_proj_1_1 + \
                 RX1[:, 1, 2] * m_proj_2_1 + \
                 tX1[:, 1]
    m_proj_2_2 = RX1[:, 2, 0] * m_proj_0_1 + \
                 RX1[:, 2, 1] * m_proj_1_1 + \
                 RX1[:, 2, 2] * m_proj_2_1 + \
                 tX1[:, 2]
    # m_proj / m_proj[2]
    x_pre = m_proj_0_2 / m_proj_2_2
    y_pre = m_proj_1_2 / m_proj_2_2
    # distort
    r2 = x_pre**2 + y_pre**2

    return x_pre, y_pre, r2