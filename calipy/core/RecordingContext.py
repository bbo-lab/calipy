# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from .utils import filehash

import imageio.v3 as iio
from ccvtools import rawio  # Also loads imageio plugins (i.e. CCV support)
from svidreader import SVidReader


class RecordingContext:

    def __init__(self, recording):
        # Reference to managed recording
        self.recording = recording

        # Collection of additional arguments passed to the reader
        self.kwargs = {}

        self.reader = SVidReader(self.recording.url)
        # The url initailly contains effects to be applied, which are trimmed away by the svidreader
        self.recording.url = self.reader.video

        # Cached filter
        self.filter = None
        self._update_filter()

    def _compute_hash(self):
        """" Compute hash of file behind current url """
        return filehash(self.recording.url)

    def _get_reader(self):
        """" Return open reader """
        return self.reader

    def _is_ffmpeg(self):
        if hasattr(self._get_reader(), 'format'):
            return self._get_reader().format.name == "FFMPEG"
        else:
            False

    def _update_filter(self):
        """" Update cached filter """
        if self.recording.filter is not None:
            # Some filtering can be done more efficiently inside ffmpeg
            if self._is_ffmpeg():
                if self.recording.filter == "HSplitLeft":
                    self.kwargs['output_params'] = ["-filter:v", "crop=iw/2:ih:0:0"]
                    self.reader = None
                    self.filter = None
                    return
                elif self.recording.filter == "HSplitRight":
                    self.kwargs['output_params'] = ["-filter:v", "crop=iw/2:ih:iw/2:0"]
                    self.reader = None
                    self.filter = None
                    return

            # Remove any previous set filter
            self.kwargs.pop('output_params', None)

            # Update current filter
            self.filter = rawio.FILTERS[self.recording.filter]

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
        suffix = ("+" + self.recording.filter) if self.recording.filter else ""
        return self.get_hash() + suffix

    def set_filter(self, filter):
        """" Update frame filter """
        self.recording.filter = self.filter = filter
        self._update_filter()

    def get_filter(self):
        return self.recording.filter

    def get_frame(self, index):
        frame = self._get_reader().get_data(index)

        if self.filter:
            return self.filter.apply(frame)

        return frame

    def get_length(self):
        if self._is_ffmpeg():
            return self.reader.count_frames()

        return self.reader.n_frames

    def get_size(self):
        return self._get_reader().get_meta_data().get('size',
                                                      self._get_reader().vprops.shape[1:3])

    def get_fps(self):
        # TODO: For ccv and some formats, it is not returning the current fps!
        mdata = self._get_reader().get_meta_data()
        if 'fps' not in mdata:
            mdata = iio.immeta(self.recording.url, plugin=self._get_reader().plugin)

        return mdata.get('fps', 60)
