# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from .CameraSystemContext import CameraSystemContext

from multiview import calib

import pickle
import yaml


class CalibrationContext(CameraSystemContext):
    """ Controller-style class to handle camera systems calibration """

    SUPPORTED_ALGORITHMS = [calib.ChArucoCalibration]
    CALIBRATION_BATCH_SIZE = 30

    def __init__(self):
        super().__init__()

        self.algorithms = [A(self) for A in self.SUPPORTED_ALGORITHMS]

        self.detections = {}
        self.calibrations = {}
        self.estimations = {}
        self.size = {}

    def get_frame(self, id):
        """ Override frame retrieval to draw calibration result """
        frame = super().get_frame(id)

        if id in self.detections and self.frame_index in self.detections[id]:
            detection = self.detections[id][self.frame_index]

            if detection:
                calibration = None
                if id in self.calibrations:
                    calibration = self.calibrations[id]

                estimation = None
                if id in self.estimations and self.frame_index in self.estimations[id]:
                    estimation = self.estimations[id][self.frame_index]

                frame = self.algorithms[0].draw(frame, detection, calibration, estimation)

        return frame

    # Detections

    def get_algorithm_names(self):
        return [a.name for a in self.algorithms]

    def run_algorithm(self, index, progress):
        if not self.session:
            return

        algorithm = self.algorithms[index]
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
                result = algorithm.detect(frame)

                if result:
                    self.detections[id][index] = result

            self.size[id] = rec.get_size()

    def calibrate_cameras(self, index, progress):
        if not self.session:
            return

        algorithm = self.algorithms[index]

        self.calibrations.clear()

        for id, detections in self.detections.items():
            total = len(detections)

            progress.setLabelText("Calibration of '{}'...".format(id))
            progress.setMaximum(total)

            calibration = None

            # Run batches with increasing size
            for batch_size in range(self.CALIBRATION_BATCH_SIZE, total, self.CALIBRATION_BATCH_SIZE):
                progress.setValue(batch_size)

                if progress.wasCanceled():
                    return

                batch = list(detections.values())[:batch_size]
                calibration = algorithm.calibrate_camera(self.size[id], batch, calibration)

            progress.setValue(total)

            # Run final optimization
            calibration = algorithm.calibrate_camera(self.size[id], detections.values(), calibration)

            if calibration:
                self.calibrations[id] = calibration

                detection_keys = list(detections.keys())

                for r in sorted(calibration['rej'], reverse=True):
                    del detection_keys[r]

                estimations = {}
                for i, k in enumerate(detection_keys):
                    estimations[k] = {'R': calibration['Rs'][i], 't': calibration['ts'][i]}

                self.estimations[id] = estimations

            if progress.wasCanceled():
                return

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

    def get_calibration_errors(self):
        errors = {}

        for id, calibration in self.calibrations.items():
            errors[id] = calibration['err']

        return errors
