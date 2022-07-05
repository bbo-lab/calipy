# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import autograd.numpy as np

import cv2


def make_corners_array(corners_all, ids_all, n_corners, frames_masks):
    used_frames_mask = np.any(frames_masks, axis=0)
    used_frame_idxs = np.where(used_frames_mask)[0]

    corners = np.empty(shape=(frames_masks.shape[0], used_frames_mask.sum(), n_corners, 2), dtype=np.float32)
    corners[:] = np.NaN
    for i_cam, frames_mask_cam in enumerate(frames_masks):
        frame_idxs_cam = np.where(frames_mask_cam)[0]

        for i_frame, f_idx in enumerate(used_frame_idxs):
            # print(ids_all[i_cam][i_frame].ravel())
            # print(corners[i_cam, f_idx].shape)
            # print(corners_all[i_cam][i_frame].shape)
            cam_fr_idx = np.where(frame_idxs_cam == f_idx)[0]
            if cam_fr_idx.size < 1:
                continue

            cam_fr_idx = int(cam_fr_idx)
            if ids_all is None:
                corners[i_cam, i_frame] = \
                    corners_all[i_cam][cam_fr_idx][:, 0, :]
            else:
                corners[i_cam, i_frame][ids_all[i_cam][cam_fr_idx].ravel(), :] = \
                    corners_all[i_cam][cam_fr_idx][:, 0, :]
    return corners


def corners_array_to_ragged(corners_array):
    corner_shape = corners_array.shape[2]

    ids_use = [np.where(~np.isnan(c[:, 1]))[0].astype(np.int32).reshape(-1, 1) for c in corners_array]
    corners_use = [c[i, :].astype(np.float32).reshape(-1, 1, corner_shape) for c, i in zip(corners_array, ids_use)]

    return corners_use, ids_use


def make_board(board_params):
    board = cv2.aruco.CharucoBoard_create(*board_params['board_size'],  # noqa
                                          *board_params['marker_size'],
                                          cv2.aruco.getPredefinedDictionary(  # noqa
                                              board_params['dictionary_id']))

    return board
