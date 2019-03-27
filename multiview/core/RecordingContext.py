# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

from .utils import filehash

import imageio
import multiview.imageio as mvio # Load imageio plugins


class RecordingContext:

    def __init__(self, recording):
        # Reference to managed recording
        self.recording = recording

        # Cached reader
        self.reader = None
        # Cached filter
        self.filter = None

    def _compute_hash(self):
        """" Compute hash of file behind current url """
        return filehash(self.recording.url)

    def _get_reader(self):
        """" Return cached reader or open reader if none cached """
        if not self.reader:
            self.reader = imageio.get_reader(self.recording.url)
            self._update_filter()

        return self.reader

    def _update_filter(self):
        """" Update cached filter """
        if self.recording.filter is not None:
            self.filter = mvio.FILTERS[self.recording.filter] # Todo: Catch use of unknown filter here

    def get_hash(self):
        """' Get hash of file or compute it if unknown """
        if self.recording.hash is None:
            self.recording.hash = self._compute_hash()

        return self.recording.hash

    def check_hash(self):
        """" Check if hash is valid. If hash is unknown, hash is computed twice and compared """
        return self.get_hash() == self._compute_hash()

    def get_source_id(self):
        """" Generate unique source identifier """
        return self.get_hash() + (":" + self.recording.filter if self.recording else "")

    def set_filter(self, filter):
        """" Update frame filter """
        self.recording.filter = filter
        self._update_filter()

    def get_frame(self, index):
        frame = self._get_reader().get_data(index)

        if self.filter:
            return self.filter.apply(frame)

        return frame

    def get_length(self):
        return self._get_reader().get_length()

    def get_size(self):
        return self._get_reader().get_data(0).shape
