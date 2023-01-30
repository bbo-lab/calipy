# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1
import copy

import pickle

import cv2

import numpy as np

from .BaseContext import BaseContext

from calipy import detect, calib, math, SOFTWARE, VERSION

from pathlib import Path


class CalibrationContext(BaseContext):
    """ Controller-style class to handle camera systems calibration """

    DETECTORS = [detect.ChArucoDetector]

    MODELS = [calib.PinholeCameraModel, calib.SphericalCameraModel]

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
        self.size = {}  # src_id > (w, h)
        self.board_params = {}  # det_id > { <detector specific> }

        self.calibrations = {}  # mod_id > cam_id > { rvec: vec3, tvec: vec3, <calibration specific> }
        self.estimations = {}  # mod_id > src_id > frm_idx > { rvec: vec3, tvec: vec3 }

        self.calibrations_multi = {}  # mod_id > cam_id > { rX1: vec3, tX1: vec3, <calibration specific> }
        # mod_id > { refcam_id, opt_result, intrinsic_flags }

        # Assumed single source for each camera
        # TODO: Add another identifier a level after or before mod_id to identify the corresponding session.
        self.estimations_boards = {}  # mod_id > frm_idx > { r1: vec3, t1: vec3 }

        self.other = {}

    def get_available_subsets(self):
        """ Override available subsets to add calibration based subsets"""
        subsets = super().get_available_subsets()

        # Add detections and estimations as subset
        detections = self.get_current_detections()
        det_idx = set()

        estimations = self.get_current_estimations()
        est_idx = set()

        for rec in self.recordings.values():
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
                estimation = self.get_current_estimations_boards().get(self.frame_index, None)

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

    @staticmethod
    def set_current_board_parameter(name, value):
        print("{}: {}".format(name, value))

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

    def save_result(self, url):
        with open(url, "wb") as file:
            temp = {'software': SOFTWARE,
                    'version': VERSION,

                    'size': self.size,
                    'board_params': self.board_params,
                    'detections': self.detections,
                    'calibrations': self.calibrations,
                    'estimations': self.estimations,
                    'calibrations_multi': self.calibrations_multi,
                    'estimations_boards': self.estimations_boards,
                    'other': self.other}
            pickle.dump(temp, file)

    def load_result(self, url):
        with open(url, "rb") as file:
            temp = pickle.load(file)

            self.detections.update(temp['detections'])
            self.size.update(temp['size'])
            self.board_params = temp.get('board_params', {})

            self.calibrations.update(temp['calibrations'])
            self.estimations.update(temp['estimations'])

            self.calibrations_multi = temp.get('calibrations_multi', {})
            self.estimations_boards = temp.get('estimations_boards', {})
            self.other = temp.get('other', {})

    def load_result_npy(self, url):
        """Read calibration results from .npy file generated by calibcam"""

        temp_npy = np.load(url, allow_pickle=True).item()

        if temp_npy['info']['opts']['free_vars']['xi']:
            camera_model_id = "opencv-omnidir"
        else:
            camera_model_id = "opencv-pinhole"

        used_frame_indices = temp_npy['info']['used_frames_ids']
        rvecs_boards = temp_npy['info']['rvecs_boards']
        tvecs_boards = temp_npy['info']['tvecs_boards']
        corners = temp_npy['info']['corners']
        # fun = temp_npy['info']['fun_final']

        calibs_single = temp_npy['info']['other']['calibs_single']

        detector = self.get_current_detector()
        self.board_params[detector.ID] = detector.board_params_calipy(temp_npy)
        self.detections[detector.ID] = {}

        for index, model in enumerate(self.models):
            if camera_model_id in model.ID:
                self.model_index = index

        model = self.get_current_model()
        self.calibrations[model.ID] = {}
        self.estimations[model.ID] = {}
        self.calibrations_multi[model.ID] = {}
        self.estimations_boards[model.ID] = {}

        rec_file_names = [Path(file).stem for file in temp_npy['rec_file_names']]
        for cam_id, rec in self.recordings.items():
            rec_name = Path(rec.recording.url).stem
            if rec_name in rec_file_names:
                calibcam_cam_idx = rec_file_names.index(rec_name)
                src_id = rec.get_source_id()

                self.size[src_id] = rec.get_size()

                frames_mask_cam = calibs_single[calibcam_cam_idx]['frames_mask']
                self.calibrations[model.ID][cam_id] = calibs_single[calibcam_cam_idx]
                self.calibrations_multi[model.ID][cam_id] = temp_npy['calibs'][calibcam_cam_idx]

                self.detections[detector.ID][src_id] = {}
                self.estimations[model.ID][src_id] = {}
                for index, frm_idx in enumerate(used_frame_indices):
                    self.detections[detector.ID][src_id][frm_idx] = detector.extract_calibcam(
                        corners[calibcam_cam_idx, index])

                    if frames_mask_cam[index]:
                        self.estimations[model.ID][src_id][frm_idx] = {
                            'rvec': calibs_single[calibcam_cam_idx]['rvecs'][index],
                            'tvec': calibs_single[calibcam_cam_idx]['tvecs'][index]}

        for index, frm_idx in enumerate(used_frame_indices):
            self.estimations_boards[model.ID][frm_idx] = {'rvec_board': rvecs_boards[index],
                                                          'tvec_board': tvecs_boards[index]}

    def clear_result(self):
        self.detections.clear()
        self.size.clear()

        self.calibrations.clear()
        self.estimations.clear()

        self.calibrations_multi.clear()
        self.estimations_boards.clear()

    # Run current detection

    def run_detection(self, board_params, progress):
        if not self.session:
            raise RuntimeError("No session selected")

        detector = self.get_current_detector()
        detector.configure(board_params)
        self.board_params[detector.ID] = board_params

        for cam_id, rec in self.recordings.items():
            src_id = rec.get_source_id()

            progress.setLabelText("Processing data from '{}'...".format(cam_id))
            progress.setMaximum(rec.get_length())

            # Clear last result
            self.detections.setdefault(detector.ID, {})[src_id] = {}

            for index in range(rec.get_length()):
                progress.setValue(index)

                if progress.wasCanceled():
                    return

                frame = rec.get_frame(index)
                result = detector.detect(frame)

                if result:
                    self.detections[detector.ID][src_id][index] = result

            self.size[src_id] = rec.get_size()

    # Run current calibration

    def prepare_corners(self, board_params, detections):

        detector = self.get_current_detector()
        detector.configure(board_params)

        corners_cam = []
        ids_cam = []
        rej = []

        for index, detected in enumerate(detections):

            if index % 20 != 0:
                rej.append(index)
                continue

            if 'square_corners' not in detected:
                rej.append(index)
                continue

            # Current backend expect at least 4 points per pattern
            # Updated 4 to min_det_feats
            if len(detected['square_corners']) < detector.min_det_feats:
                rej.append(index)
                continue

            # Make sure detected points are not all on one line
            extracted = detector.extract(detected)
            if math.are_points_on_line(extracted['object_pts']):
                rej.append(index)
                continue

            # Check if consecutive frames are too similar
            if len(corners_cam):
                previous_pts = np.zeros((detector.num_feats, 2), dtype=np.float64)
                current_pts = np.zeros((detector.num_feats, 2), dtype=np.float64)
                previous_pts[ids_cam[-1].ravel()] = corners_cam[-1].squeeze()
                current_pts[detected['square_ids'].ravel()] = detected['square_corners'].squeeze()

                diff = current_pts - previous_pts
                ids_use = np.intersect1d(ids_cam[-1].ravel(), detected['square_ids'].ravel())
                diff = diff[ids_use]
                dist = np.sqrt(np.sum(diff ** 2, 1))

                # Use frame when all ids are different
                if np.size(dist) == 0:
                    dist_max = np.inf
                else:
                    dist_max = np.max(dist)
                # Check if maximum distance is greater than one pixel
                if dist_max < 1.0:
                    # Reject the frame if it has fewer or equal features than the previous frame
                    if len(detected['square_ids'].ravel()) <= len(ids_cam[-1].ravel()):
                        rej.append(index)
                        continue

            corners_cam.append(detected['square_corners'])
            ids_cam.append(extracted['square_ids'])

        return corners_cam, ids_cam, rej

    def calibrate_cameras(self, progress):
        model = self.get_current_model()

        source_maps = self.get_all_source_ids()
        detections_all = self.get_current_detections()
        board_params = self.get_current_board_params()

        if progress.wasCanceled():
            return

        num_frames = [rec.get_length() for rec in self.recordings.values()]
        num_frames = min(num_frames)

        sizes = []
        frames_masks = np.zeros(shape=(len(self.get_cameras()), num_frames), dtype=bool)
        corners_all = []
        ids_all = []
        rejected_indices_all = []

        for cam_idx, cam in enumerate(self.get_cameras()):
            # Retrieve all sources for cameras
            src_id = [src_map[cam.id] for src_map in source_maps if cam.id in src_map][0]
            rec = self.recordings[cam.id]
            sizes.append(self.size[src_id])

            # Extract detection object and image points
            rejected_indices = []

            detections = detections_all.get(src_id, {})
            detection_keys = [(src_id, idx) for idx in detections if idx < num_frames]
            detection_values = list(detections.values())[:len(detection_keys)]

            corners_cam, ids_cam, rejections = self.prepare_corners(board_params, detection_values)

            for r in sorted(rejections, reverse=True):
                rejected_indices.append(detection_keys[r])
                del detection_keys[r]

            rejected_indices_all.append(rejected_indices)
            used_frame_indices_cam = [idx for (src_id, idx) in detection_keys]
            frames_masks[cam_idx, np.array(used_frame_indices_cam)] = True

            corners_all.append(corners_cam)
            ids_all.append(ids_cam)

        # All the src_ids have same board/detection parameteres!
        model.configure(board_params)

        try:
            calibs_single = model.perform_single_cam_calibrations(corners_all, ids_all, sizes, frames_masks)
        except Exception as e:
            print("ERROR: " + str(e))
            raise RuntimeError

        used_frame_indices = np.where(np.any(frames_masks, axis=0))[0]
        for cam_idx, cam in enumerate(self.get_cameras()):
            # Save calibration and estimation if successful

            src_id = [src_map[cam.id] for src_map in source_maps if cam.id in src_map][0]
            calibration = calibs_single[cam_idx]

            used_frame_indices_cam = np.where(frames_masks[cam_idx, :])[0]
            rejected_indices = rejected_indices_all[cam_idx]
            calibration['rej'] = rejected_indices  # Needed for stats

            self.other[model.ID] = {'corners_all': corners_all,
                                    'ids_all': ids_all,
                                    'frames_masks': frames_masks}
            self.calibrations.setdefault(model.ID, {})[cam.id] = calibration

            if 'idx' in calibration:
                used_frame_indices_cam = [used_frame_indices_cam[i] for i in calibration['idx'].flatten()]

            self.estimations.setdefault(model.ID, {})[src_id] = {}

            for frm_idx in used_frame_indices_cam:
                index = np.where(used_frame_indices == frm_idx)[0][0]
                self.estimations[model.ID][src_id][frm_idx] = {'rvec': calibration['rvecs'][index],
                                                               'tvec': calibration['tvecs'][index]}

        if progress.wasCanceled():
            return

    # Run system calibration

    def calibrate_system(self, progress):

        model = self.get_current_model()
        board_params = self.get_current_board_params()
        calibrations_all = self.get_current_calibrations()

        model.configure(board_params)

        if progress.wasCanceled():
            return

        if not bool(calibrations_all):
            raise Exception("Please, Calibrate Cameras.")

        num_cams = len(self.get_cameras())
        if num_cams < 2:
            raise Exception("There are less than two cameras. Calibrate System not applicable.")

        other = self.other.get(model.ID, self.other)
        calibs_single = [calib_cam for calib_cam in calibrations_all.values()]
        corners_all = other['corners_all']
        ids_all = other['ids_all']
        frames_masks = other['frames_masks']

        # Run system calibration
        calibs_fit, rvecs_boards, tvecs_boards, min_result, residuals, args = \
            model.perform_multi_calibration(calibs_single, corners_all, ids_all, frames_masks)

        # Save calibration and estimations if successful
        if min_result.success:

            for cam_idx, (cam) in enumerate(self.get_cameras()):
                calibs_fit[cam_idx].update({'mean_res': np.nanmean(residuals[cam_idx]),
                                            'med_res': np.nanmedian(residuals[cam_idx]),
                                            'max_res': np.nanmax(residuals[cam_idx])
                                            })
                self.calibrations_multi.setdefault(model.ID, {})[cam.id] = calibs_fit[cam_idx]

            if model.ID not in self.estimations_boards:
                self.estimations_boards[model.ID] = {}

            used_frame_indices = np.where(np.any(frames_masks, axis=0))[0]
            for index, frm_idx in enumerate(used_frame_indices):
                self.estimations_boards[model.ID][frm_idx] = {'rvec_board': rvecs_boards[index],
                                                              'tvec_board': tvecs_boards[index]}

            self.other[model.ID]['cost_val_final'] = min_result.cost
            self.other[model.ID]['optimality_final'] = min_result.optimality

        else:
            raise Exception("Optimisaiton algorithm failed to converge!")

    # Results statistics

    def get_detection_stats(self):
        stats = {}

        detections = self.get_current_detections()

        for cam_id, rec in self.recordings.items():
            src_id = rec.get_source_id()

            # Skip detection that were never run
            if src_id not in detections:
                continue

            # Count detections and markers
            patterns = 0
            markers = 0

            for detected in detections[src_id].values():
                if 'square_corners' in detected:
                    patterns += 1
                    markers += len(detected.get('marker_corners', []))

            stats[cam_id] = (patterns, markers)

        return stats

    def get_calibration_stats(self):
        stats = {}

        source_maps = self.get_all_source_ids()

        detections = self.get_current_detections()
        det_stats = self.get_detection_stats()

        calibrations = self.get_current_calibrations()
        estimations = self.get_current_estimations()

        calibrations_multi = self.get_current_calibrations_multi()

        for cam_id, calibration in calibrations.items():
            source_ids = [src_map[cam_id] for src_map in source_maps if cam_id in src_map]

            orig_count_det = sum([len(detections.get(sid, [])) for sid in source_ids])
            count_det = det_stats[cam_id][0]

            count_est = sum([len(estimations.get(sid, [])) for sid in source_ids])
            count_rej = len(calibration.get('rej', []))

            stats[cam_id] = {
                'error': calibration.get('repro_error', 0),
                'detections': count_det,
                'usable': orig_count_det - count_rej,
                'estimations': count_est,
            }

            if 'med_res' in calibrations_multi.get(cam_id, {}):
                stats[cam_id].update({'system_errors': (calibrations_multi[cam_id]['max_res'],
                                                        calibrations_multi[cam_id]['med_res'])
                                      })
        return stats
