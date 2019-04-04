# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from .BaseContext import BaseContext

from multiview import detect
from multiview import calib

import pickle
import cv2


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
        self.detections = {}
        self.calibrations = {}
        self.estimations = {}
        self.size = {}

    def get_frame(self, id):
        """ Override frame retrieval to draw calibration result """
        frame = super().get_frame(id)

        detection = self.detections.get(id, {}).get(self.frame_index, None)
        if detection:
            # Make sure we draw in color by converting the frame to color first if necessary
            if frame.ndim < 3 or frame.shape[2] == 1:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

            # Draw detection result
            frame = self.get_detector().draw(frame, detection)

            calibration = self.calibrations.get(id, None)
            estimation = self.estimations.get(id, {}).get(self.frame_index, None)

            # Draw calibration result
            frame = self.get_model().draw(frame, detection, calibration, estimation)

        return frame

    # Availability info

    def get_detector_names(self):
        return [a.NAME for a in self.detectors]

    def select_detector(self, index):
        self.detector_index = index

    def get_detector(self):
        return self.detectors[self.detector_index]

    def get_model_names(self):
        return [a.NAME for a in self.models]

    def select_model(self, index):
        self.model_index = index

    def get_model(self):
        return self.models[self.model_index]

    # Detection

    def run_detection(self, progress):
        if not self.session:
            return
        
        detector = self.get_detector()
        recordings = self.recordings

        self.detections.clear()

        for id, rec in recordings.items():

            progress.setLabelText("Processing data from '{}'...".format(id))
            progress.setMaximum(rec.get_length())

            self.detections[id] = {}

            for index in range(rec.get_length()):
                progress.setValue(index)

                if progress.wasCanceled():
                    return

                frame = rec.get_frame(index)
                result = detector.detect(frame)

                if result:
                    self.detections[id][index] = result

            self.size[id] = rec.get_size()

    def calibrate_cameras(self, progress):
        if not self.session:
            return

        model = self.get_model()

        self.calibrations.clear()

        for id, detections in self.detections.items():
            total = len(detections)

            progress.setLabelText("Calibration of '{}'...".format(id))
            progress.setMaximum(total)

            calibration = None

            # Run batches with increasing size
            for batch_size in range(total // 5, total, (total // 5) + 1):
                progress.setValue(batch_size)

                if progress.wasCanceled():
                    return

                batch = list(detections.values())[:batch_size]
                try:
                    calibration = model.calibrate_camera(self.size[id], batch, calibration)
                except Exception as e:
                    print("Batch Calibration with {:d} / {:d} detections failed: {:s}".format(batch_size, total, str(e)))

            progress.setValue(total)

            # Run final optimization
            calibration = model.calibrate_camera(self.size[id], detections.values(), calibration)

            if calibration:
                self.calibrations[id] = calibration

                detection_keys = list(detections.keys())

                for r in sorted(calibration['rej'], reverse=True):
                    del detection_keys[r]

                if 'idx' in calibration:
                    detection_keys = [detection_keys[i] for i in calibration['idx'].flatten()]

                estimations = {}
                for i, k in enumerate(detection_keys):
                    estimations[k] = {'R': calibration['Rs'][i], 't': calibration['ts'][i]}

                self.estimations[id] = estimations

            if progress.wasCanceled():
                return

    def calibrate_system(self, progress):
        pass

    # Results

    def save_result(self, url):
        with open(url, "wb") as file:
            temp = {'detections': self.detections,
                    'calibrations': self.calibrations,
                    'estimations': self.estimations,
                    'size': self.size}
            pickle.dump(temp, file)

    def load_result(self, url):
        with open(url, "rb") as file:
            temp = pickle.load(file)
            self.detections = temp['detections']
            self.calibrations = temp['calibrations']
            self.estimations = temp['estimations']
            self.size = temp['size']

    def clear_result(self):
        self.detections.clear()
        self.calibrations.clear()
        self.estimations.clear()
        self.size.clear()

    def get_detection_stats(self):
        stats = {}

        for id, detections in self.detections.items():
            patterns = 0
            markers = 0
            for detected in detections.values():
                if 'square_corners' in detected:
                    patterns += 1
                    markers += len(detected['marker_corners'])

            stats[id] = (patterns, markers)

        return stats

    def get_calibration_stats(self):
        stats = {}

        for id, calibration in self.calibrations.items():
            detections = len(self.detections.get(id, []))
            rejections = len(calibration['rej'])

            stats[id] = {
                'error': calibration['err'],
                'detections': detections,
                'usable': detections - rejections,
                'estimations': len(self.estimations.get(id, []))
            }

        return stats
