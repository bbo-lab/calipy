# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from .CameraSystemContext import CameraSystemContext

from multiview import calib

import pickle
import yaml


class CalibrationContext(CameraSystemContext):
    """ Controller-style class to handle camera systems calibration """

    SUPPORTED_ALGORITHMS = [calib.ChArucoCalibration]

    def __init__(self):
        super().__init__()

        self.algorithms = [A(self) for A in self.SUPPORTED_ALGORITHMS]

        self.result = {}

    def get_frame(self, id):

        frame = super().get_frame(id)

        if id in self.result and self.frame_index in self.result[id]:
            result = self.result[id][self.frame_index]

            if result:
                frame = self.algorithms[0].draw(frame, result)

        return frame

    # Detections

    def get_algorithm_names(self):
        return [a.name for a in self.algorithms]

    def run_algorithm(self, index):
        if not self.session:
            return

        algorithm = self.algorithms[index]
        recordings = self.recordings

        self.result.clear()

        for id, rec in recordings.items():

            self.result[id] = {}

            for index in range(rec.get_length()):
                frame = rec.get_frame(index)
                result = algorithm.detect(frame)

                if result:
                    self.result[id][index] = result

    # Results

    def save_result(self, url):
        with open(url, "wb") as file:
            pickle.dump(self.result, file)

    def load_result(self, url):
        with open(url, "rb") as file:
            self.result = pickle.load(file)

    def get_result_stats(self):
        stats = {}

        for id, detections in self.result.items():
            patterns = 0
            markers = 0
            for detected in detections.values():
                if 'square_corners' in detected:
                    patterns += 1
                    markers += len(detected['marker_corners'])

            stats[id] = (patterns, markers)

        return stats

