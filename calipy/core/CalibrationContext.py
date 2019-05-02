# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import pickle

import cv2

from .BaseContext import BaseContext

from calipy import detect, calib, math


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

        # Initialize results
        self.detections = {}  # det_id > src_id > frm_idx > { <detector specific> }
        self.size = {}  # src_id > (w, h)
        self.detection_params = {} # det_id > src_id > { <detector specific> }

        self.calibrations = {}  # mod_id > cam_id > { R: vec3, t: vec3, <calibration specific> }
        self.estimations = {}  # mod_id > src_id > frm_idx > { R: vec3, t: vec3 }

        self.syscal = {} # Temp

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

    def get_frame(self, id):
        """ Override frame retrieval to draw calibration result """
        frame = super().get_frame(id)
        src_id = self.get_source_id(id)

        #if id in self.calibrations:
        #    frame = self.get_current_model().undistort(frame, self.calibrations[id])

        detection = self.get_current_detections().get(src_id, {}).get(self.frame_index, None)
        if detection:
            # Make sure we draw in color by converting the frame to color first if necessary
            if frame.ndim < 3 or frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            # Draw detection result
            frame = self.get_current_detector().draw(frame, detection)

            calibration = self.get_current_calibrations().get(id, None)
            estimation = self.get_current_estimations().get(src_id, {}).get(self.frame_index, None)

            # Draw calibration result
            frame = self.get_current_model().draw(frame, detection, calibration, estimation)

        return frame

    # Detector and detection management

    def get_detector_names(self):
        return [a.NAME for a in self.detectors]

    def select_detector(self, index):
        self.detector_index = index

    def set_current_detector_parameter(self, name, value):
        print("{}: {}".format(name, value))

    def get_current_detector(self):
        return self.detectors[self.detector_index]

    def get_current_detector_params(self):
        return self.detection_params.get(self.get_current_detector().ID, {})

    def get_current_detections(self):
        return self.detections.get(self.get_current_detector().ID, {})

    # Model and calibration management

    def get_model_names(self):
        return [a.NAME for a in self.models]

    def select_model(self, index):
        self.model_index = index

    def get_current_model(self):
        return self.models[self.model_index]

    def get_current_calibrations(self):
        return self.calibrations.get(self.get_current_model().ID, {})

    def get_current_estimations(self):
        return self.estimations.get(self.get_current_model().ID, {})

    # Overall reault management

    def save_result(self, url):
        with open(url, "wb") as file:
            temp = {'detections': self.detections,
                    'size': self.size,
                    'detection_params': self.detection_params,
                    'calibrations': self.calibrations,
                    'estimations': self.estimations,
                    'syscal': self.syscal}
            pickle.dump(temp, file)

    def load_result(self, url):
        with open(url, "rb") as file:
            temp = pickle.load(file)

            for cam in self.get_cameras():
                if cam.id in self.recordings:
                    src_id = self.recordings[cam.id].get_source_id()

                    if cam.id in temp['detections']:
                        det_id = self.get_current_detector().ID

                        self.detections.setdefault(det_id, {})[src_id] = temp['detections'].pop(cam.id)
                        self.size[src_id] = temp['size'].pop(cam.id)

                    if cam.id in temp['estimations']:
                        mod_id = self.get_current_model().ID

                        self.estimations.setdefault(mod_id, {})[src_id] = temp['estimations'].pop(cam.id)

                if cam.id in temp['calibrations']:
                    mod_id = self.get_current_model().ID

                    self.calibrations.setdefault(mod_id, {})[cam.id] = temp['calibrations'].pop(cam.id)

            self.detections.update(temp['detections'])
            self.size.update(temp['size'])
            self.detection_params = temp.get('detection_params', {})

            self.calibrations.update(temp['calibrations'])
            self.estimations.update(temp['estimations'])

            self.syscal = temp.get('syscal', {})

    def cleanup_result(self):
        """ Delete any results from unmatched source id """
        pass

    def clear_result(self):
        self.detections.clear()
        self.size.clear()

        self.calibrations.clear()
        self.estimations.clear()

        self.syscal.clear()

    # Run current detection

    def run_detection(self, parameters, progress):
        if not self.session:
            raise RuntimeError("No session selected")

        detector = self.get_current_detector()
        detector.configure(parameters)

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

            self.detection_params.setdefault(detector.ID, {})[src_id] = parameters

            # TODO: Check for collisions
            self.size[src_id] = rec.get_size()

    # Run current calibration

    def prepare_detections(self, parameters, detections):

        detector = self.get_current_detector()
        detector.configure(parameters)

        obj_pts = []
        img_pts = []
        rej = []

        for index, detected in enumerate(detections):
            extracted = detector.extract(detected)

            if not extracted:
                rej.append(index)
                continue

            # Current backend expect at least 4 points per pattern
            if len(extracted['img_pts']) < 4:
                rej.append(index)
                continue

            # Make sure detected points are not all on one line
            if math.are_points_on_line(extracted['obj_pts']):
                rej.append(index)
                continue

            obj_pts.append(extracted['obj_pts'])
            img_pts.append(extracted['img_pts'])

        return obj_pts, img_pts, rej

    def calibrate_cameras(self, progress):
        model = self.get_current_model()

        source_maps = self.get_all_source_ids()
        detections_all = self.get_current_detections()
        parameters_all = self.get_current_detector_params()

        for cam in self.get_cameras():
            # Retrieve all sources for cameras
            source_ids = [src_map[cam.id] for src_map in source_maps if cam.id in src_map]

            # Extract detection object and image points
            object_points = []
            image_points = []
            used_indices = []
            rejected_indices = []
            for src_id in source_ids:
                detections = detections_all.get(src_id, {})

                detection_keys = [(src_id, idx) for idx in detections]
                detection_values = list(detections.values())

                parameters = parameters_all.get(src_id, {})

                obj_pts, img_pts, rejections = self.prepare_detections(parameters, detection_values)

                object_points += obj_pts
                image_points += img_pts

                for r in sorted(rejections, reverse=True):
                    rejected_indices.append(detection_keys[r])
                    del detection_keys[r]

                used_indices += detection_keys

            sizes = [self.size[sid] for sid in source_ids]

            total = len(object_points)

            progress.setLabelText("Calibration of '{}'...".format(cam.id))
            progress.setMaximum(total)

            calibration = None

            # Run batches with increasing size
            for batch_size in range(total // 5, total, (total // 5) + 1):
                progress.setValue(batch_size)

                if progress.wasCanceled():
                    return

                print("Calibration of {} with {} / {} detections".format(cam.id, batch_size, total))

                try:
                    calibration = model.calibrate_camera(sizes[0], object_points[:batch_size], image_points[:batch_size], calibration)
                except Exception as e:
                    print("Batch Calibration with {:d} / {:d} detections failed: {:s}".format(batch_size, total, str(e)))

            progress.setValue(total)

            print("Calibration of {} with all {} detections".format(cam.id, total))

            # Run final optimization
            calibration = model.calibrate_camera(sizes[0], object_points, image_points, calibration)

            # Save calibration and estimation if successfull
            if calibration:
                calibration['rej'] = rejected_indices  # Needed for stats

                self.calibrations.setdefault(model.ID, {})[cam.id] = calibration

                if 'idx' in calibration:
                    used_indices = [used_indices[i] for i in calibration['idx'].flatten()]

                for src_id in source_ids:
                    self.estimations.setdefault(model.ID, {})[src_id] = {}

                for index, (src_id, frm_idx) in enumerate(used_indices):
                    self.estimations[model.ID][src_id][frm_idx] = {'R': calibration['Rs'][index],
                                                                   't': calibration['ts'][index]}

            if progress.wasCanceled():
                return

    def calibrate_system(self, progress):
        model = self.get_current_model()

        self.syscal = model.calibrate_system(self.size, self.detections, self.calibrations, self.estimations)

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
                    markers += len(detected['marker_corners'])

            stats[cam_id] = (patterns, markers)

        return stats

    def get_calibration_stats(self):
        stats = {}

        source_maps = self.get_all_source_ids()

        detections = self.get_current_detections()
        calibrations = self.get_current_calibrations()
        estimations = self.get_current_estimations()

        for cam_id, calibration in calibrations.items():
            source_ids = [src_map[cam_id] for src_map in source_maps if cam_id in src_map]

            count_det = sum([len(detections.get(sid, [])) for sid in source_ids])
            count_est = sum([len(estimations.get(sid, [])) for sid in source_ids])

            count_rej = len(calibration['rej'])

            stats[cam_id] = {
                'error': calibration['err'],
                'detections': count_det,
                'usable': count_det - count_rej,
                'estimations': count_est
            }

        return stats
