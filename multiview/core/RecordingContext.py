from .utils import filehash

import imageio
import multiview.imageio as mvio # Load imageio plugins

from multiview import file


class RecordingContext:

    def __init__(self, recording):
        self.recording = recording
        self.reader = None
        self.filter = None

        self.update_filter()

    def compute_hash(self):
        return filehash(self.recording.url)

    def update_hash(self):
        self.recording.hash = self.compute_hash()

    def set_filter(self, filter):
        self.recording.filter = filter
        self.update_filter()

    def update_filter(self):
        if self.recording.filter in mvio.FILTERS:
            self.filter = mvio.FILTERS[self.recording.filter]
        else:
            print(self.recording.filter)

    # TODO: Remove method!
    def get_reader(self):
        if not self.reader:
            self.reader = imageio.get_reader(self.recording.url)

        return self.reader

    def get_frame(self, index):
        frame = self.get_reader().get_data(index)

        if self.filter:
            return self.filter.apply(frame)

        return frame

    def get_length(self):
        return self.get_reader().get_length()

    def get_size(self):
        return self.get_reader().get_data(0).shape
