# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1
import copy
import logging
from pathlib import Path

import cv2
import numpy as np
from matplotlib import pyplot as plt

from calibcamlib.yaml_helper import collection_to_array

from calipy import detect, calib, VERSION
from .BaseContext import BaseContext

logger = logging.getLogger(__name__)


class CalibrationContext(BaseContext):
    """ Controller-style class to handle camera systems calibration """

    DETECTORS = [detect.ChArucoDetector]

    MODELS = [calib.CameraModel]

    def __init__(self):
        super().__init__()

        # Initialize detectors and models with context
        self.detectors = [D(self) for D in self.DETECTORS]
        self.models = [M(self) for M in self.MODELS]

        # Current selection
        self.detector_index = 0
        self.model_index = 0
        self.display_calib_index = 0

        # Initialize results
        self.detections = {}  # det_id > src_id > frm_idx > { <detector specific> }
        self.board_params = {}  # det_id > { <detector specific> }

        self.calibrations = {}  # mod_id > cam_id > { rvec: vec3, tvec: vec3, <calibration specific> }
        self.estimations = {}  # mod_id > src_id > frm_idx > { rvec: vec3, tvec: vec3 }

        self.calibrations_multi = {}  # mod_id > cam_id > { rX1: vec3, tX1: vec3, <calibration specific> }
        # mod_id > { refcam_id, opt_result, intrinsic_flags }

        # Assumed single source for each camera
        self.estimations_boards = {}  # mod_id > src_id > frm_idx > { r1: vec3, t1: vec3 }

        self.other = {}

    def get_available_subsets(self):
        """ Override available subsets to add calibration based subsets"""
        subsets = super().get_available_subsets()

        if self.session:
            # Add detections and estimations as subset
            detections = self.get_current_detections()
            det_idx = set()

            estimations = self.get_current_estimations()
            est_idx = set()

            for rec in self.session.recordings.values():
                src_id = rec.get_source_id()
                det_idx.update(detections.get(src_id, []))
                est_idx.update(estimations.get(src_id, []))

            if len(det_idx):
                subsets['Detections'] = sorted(det_idx)

            if len(est_idx):
                subsets['Estimations'] = sorted(est_idx)

        return subsets

    def get_frame(self, idx):
        """ Override frame retrieval to draw calibration result """
        frame = copy.copy(super().get_frame(idx))
        src_id = self.get_source_id(idx)

        # if id in self.calibrations:
        #    frame = self.get_current_model().undistort(frame, self.calibrations[id])

        detection = self.get_current_detections().get(src_id, {}).get(self.frame_index, None)
        # Board parameters
        board_params = self.get_current_board_params()

        if detection:
            # Make sure we draw in color by converting the frame to color first if necessary
            if frame.ndim < 3 or frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            # Draw detection result
            detector = self.get_current_detector()
            detector.configure(board_params)
            frame = detector.draw(frame, detection)

            if self.display_calib_index == 0:
                calibration = self.get_current_calibrations().get(idx, None)
                estimation = self.get_current_estimations().get(src_id, {}).get(self.frame_index, None)
            else:
                calibration = self.get_current_calibrations_multi().get(idx, None)
                estimation = self.get_current_estimations_boards().get(src_id, {}).get(self.frame_index, None)

            # Draw calibration result

            model = self.get_current_model()
            model.configure(board_params)
            frame = model.draw(frame, detection, calibration, estimation)

        return frame

    # Detector and detection management

    def get_detector_names(self):
        return [a.NAME for a in self.detectors]

    def select_detector(self, index):
        self.detector_index = index

    def get_current_detector(self):
        return self.detectors[self.detector_index]

    def get_current_board_params(self):
        return copy.deepcopy(self.board_params.get(self.get_current_detector().ID, {}))

    def get_current_detections(self):
        return copy.deepcopy(self.detections.get(self.get_current_detector().ID, {}))

    # Model and calibration management

    def get_model_names(self):
        return [a.NAME for a in self.models]

    def select_model(self, index):
        self.model_index = index

    def select_display_calib(self, index):
        self.display_calib_index = index

    def get_current_model(self):
        return self.models[self.model_index]

    def get_current_calibrations(self):
        return copy.deepcopy(self.calibrations.get(self.get_current_model().ID, {}))

    def get_current_estimations(self):
        return copy.deepcopy(self.estimations.get(self.get_current_model().ID, {}))

    def get_current_calibrations_multi(self):
        return copy.deepcopy(self.calibrations_multi.get(self.get_current_model().ID, {}))

    def get_current_estimations_boards(self):
        return copy.deepcopy(self.estimations_boards.get(self.get_current_model().ID, {}))

    # Overall result management

    def load_calibration(self, calib_dict: dict):
        """Read calibration info calibcam dict, only if the corresponding recordings are already loaded"""
        if not self.session:
            return

        logger.log(logging.INFO,
                   f"Current software version: {VERSION}, Calibcam file version: {calib_dict.get('version', None)}.")

        # Assuming that all the videos in the session have different names
        # The videos have the same names, so identificaiton is changed to the dir containing the video or
        # Identifyin the unique part in the path to the video which will be used to match with the available videos.
        rec_file_names = calib_dict['rec_file_names']
        rec_file_name_parts = [list(Path(file).parts) for file in rec_file_names]
        unique_idx = 0
        for unique_idx in range(1, len(rec_file_name_parts[0])):
            part_list = [name_parts[-unique_idx] for name_parts in rec_file_name_parts]
            if len(part_list) == len(set(part_list)):
                logger.log(logging.INFO, f"Unique parts in file names: {part_list}")
                unique_idx *= -1
                break
        rec_file_unique_names = [Path(file).parts[unique_idx] for file in rec_file_names]

        # Decide the detector and camera model
        calibcam_det_id = "charuco"
        camera_model_id = "calibcam-camera"

        # Detection specific
        start_frame_indexes = calib_dict['info']['opts'].get('start_frame_indexes', [0] * len(rec_file_names))
        used_frame_indices = calib_dict['info']['used_frames_ids']
        corners = np.asarray(calib_dict['info']['corners'])

        # Single camera calibraion
        calibs_single = collection_to_array(calib_dict['info']['other']['calibs_single'])

        # Multi camera calibration
        rvecs_boards = calib_dict['info']['rvecs_boards']
        tvecs_boards = calib_dict['info']['tvecs_boards']
        if 'fun_final' in calib_dict['info']:
            final_err = np.asarray(calib_dict['info']['fun_final']).reshape(corners.shape)
            final_err = np.abs(final_err)
        else:
            final_err = np.empty(corners.shape)
            final_err[:] = np.nan

        # Set detector
        for index, detor in enumerate(self.detectors):
            if calibcam_det_id == detor.ID:
                self.detector_index = index
                break
        detector = self.get_current_detector()
        self.board_params[detector.ID] = detector.board_params_calipy(calib_dict)
        self.detections[detector.ID] = {}

        # Set camera model
        for index, model in enumerate(self.models):
            if camera_model_id == model.ID:
                self.model_index = index
                break
        model = self.get_current_model()
        self.calibrations[model.ID] = {}
        self.estimations[model.ID] = {}
        self.calibrations_multi[model.ID] = {}
        self.estimations_boards[model.ID] = {}

        # Set data
        for cam_id, rec in self.session.recordings.items():
            rec_unique_name = Path(rec.url).parts[unique_idx]
            if rec_unique_name in rec_file_unique_names:
                calibcam_cam_idx = rec_file_unique_names.index(rec_unique_name)
                src_id = rec.get_source_id()

                frames_mask_cam = calibs_single[calibcam_cam_idx]['frames_mask']
                self.calibrations[model.ID][cam_id] = calibs_single[calibcam_cam_idx]
                if len(calib_dict['calibs']):
                    self.calibrations_multi[model.ID][cam_id] = calib_dict['calibs'][calibcam_cam_idx]
                    self.calibrations_multi[model.ID][cam_id]['max_err'] = np.nanmax(final_err[calibcam_cam_idx])
                    self.calibrations_multi[model.ID][cam_id]['med_err'] = np.nanmedian(final_err[calibcam_cam_idx])
                    self.calibrations_multi[model.ID][cam_id]['mean_err'] = np.nanmean(final_err[calibcam_cam_idx])

                self.detections[detector.ID][src_id] = {}
                self.estimations[model.ID][src_id] = {}
                self.estimations_boards[model.ID][src_id] = {}
                for index, frm_idx in enumerate(used_frame_indices):
                    frm_idx += start_frame_indexes[calibcam_cam_idx]
                    self.detections[detector.ID][src_id][frm_idx] = detector.extract_calibcam(
                        corners[calibcam_cam_idx, index])

                    if frames_mask_cam[index]:
                        self.estimations[model.ID][src_id][frm_idx] = {
                            'rvec': calibs_single[calibcam_cam_idx]['rvecs'][index],
                            'tvec': calibs_single[calibcam_cam_idx]['tvecs'][index]}

                    if len(rvecs_boards):
                        self.estimations_boards[model.ID][src_id][frm_idx] = {'rvec_board': rvecs_boards[index],
                                                                              'tvec_board': tvecs_boards[index],
                                                                              'max_err': np.nanmax(
                                                                                  final_err[calibcam_cam_idx, index]),
                                                                              'med_err': np.nanmedian(
                                                                                  final_err[calibcam_cam_idx, index]),
                                                                              'mean_err': np.nanmean(
                                                                                  final_err[calibcam_cam_idx, index])}

    def clear_result(self):
        self.detections.clear()

        self.calibrations.clear()
        self.estimations.clear()

        self.calibrations_multi.clear()
        self.estimations_boards.clear()

    # Results statistics

    def get_detection_stats(self):
        stats = {}

        detections = self.get_current_detections()

        for cam_id, rec in self.session.recordings.items():
            src_id = rec.get_source_id()

            # Skip detection that were never run
            if src_id not in detections:
                continue

            # Count detections and markers
            patterns = 0
            markers = 0

            for detected in detections[src_id].values():
                if len(detected.get('square_corners', [])):
                    patterns += 1
                    markers += len(detected.get('square_corners', []))

            stats[cam_id] = (patterns, markers)

        return stats

    def get_calibration_stats(self):
        stats = {}

        source_maps = self.get_current_source_ids()

        det_stats = self.get_detection_stats()

        calibrations = self.get_current_calibrations()
        estimations = self.get_current_estimations()

        calibrations_multi = self.get_current_calibrations_multi()
        estimations_board = self.get_current_estimations_boards()

        for cam_id, calibration in calibrations.items():
            source_id = source_maps.get(cam_id, None)

            count_det = det_stats.get(cam_id, (0, 0))[0]
            count_est = len(estimations.get(source_id, []))

            stats[cam_id] = {
                'error': calibration.get('repro_error', 0),  # Provided by OpenCV
                'detections': count_det,
                'single_estimations': count_est,
            }
            if 'med_err' in calibrations_multi.get(cam_id, {}):
                stats[cam_id].update({'system_errors': (calibrations_multi[cam_id]['mean_err'],
                                                        calibrations_multi[cam_id]['med_err'],
                                                        calibrations_multi[cam_id]['max_err'])
                                      })

            estimations_cam = estimations_board.get(source_id, {})
            if 'med_err' in estimations_cam.get(self.frame_index, {}):
                stats[cam_id].update({'system_frame_errors': (estimations_cam[self.frame_index]['mean_err'],
                                                              estimations_cam[self.frame_index]['med_err'],
                                                              estimations_cam[self.frame_index]['max_err'])
                                      })
        return stats

    def plot_system_calibration_errors(self):
        source_maps = self.get_current_source_ids()

        calibrations = self.get_current_calibrations()
        estimations_board = self.get_current_estimations_boards()

        fig, axs = plt.subplots(len(calibrations.keys()), sharex=True)
        if not isinstance(axs, np.ndarray):
            axs = [axs]
        for i, (cam_id, calibration) in enumerate(calibrations.items()):
            source_id = source_maps.get(cam_id, None)
            estimations_cam = estimations_board.get(source_id, {})
            frames_cam = []
            errors_cam = [[] for _ in range(3)]
            for frame_idx, estimation in estimations_cam.items():
                if 'med_err' in estimation:
                    frames_cam.append(frame_idx)
                    errors_cam[0].append(estimation['mean_err'])
                    errors_cam[1].append(estimation['med_err'])
                    errors_cam[2].append(estimation['max_err'])

            axs[i].plot(frames_cam, errors_cam[0], '*-', label='mean')
            axs[i].plot(frames_cam, errors_cam[1], '*-', label='median')
            axs[i].plot(frames_cam, errors_cam[2], '*-', label='max')
            axs[i].set_title(cam_id)
            axs[i].legend()

        plt.show()
