# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1
import imageio
from ccvtools import rawio  # Also loads imageio plugins (i.e. CCV support)
from svidreader import filtergraph

from .utils import filehash


class RecordingContext:

    def __init__(self, recording):
        # Reference to managed recording
        self.recording = recording
        print("The recording url is", recording.url)
        reader = filtergraph.get_reader(recording.url, cache=True, backend='iio')
        if recording.pipeline is not None:
            print("The recording pipeline is", recording.pipeline)
            reader = filtergraph.create_filtergraph_from_string([reader], pipeline=recording.pipeline)['out']
        self.reader = reader

        # Collection of additional arguments passed to the reader
        self.kwargs = {}

        # Reference to managed recording
        self.video_path = recording.url

        # Cached filter
        self.filter = None
        self._update_filter()

    def _compute_hash(self):
        """" Compute hash of file behind current url """
        return filehash(self.video_path)

    def _get_reader(self):
        """" Return open reader """
        return self.reader

    def _update_filter(self):
        """" Update cached filter """
        if self.recording.filter is not None:

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
        return self.reader.n_frames

    def get_size(self):
        return self._get_reader().get_meta_data().get('size',
                                                      self.get_frame(0).shape[:2][::-1])

    def get_fps(self):
        mdata = self._get_reader().get_meta_data()
        if 'fps' in mdata:
            return mdata.get('fps')
        else:
            return imageio.get_reader(self.video_path).get_meta_data().get('fps', 60)
