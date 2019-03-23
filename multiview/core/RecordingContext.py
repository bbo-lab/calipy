from .utils import filehash

import imageio
import multiview.imageio # Load imageio plugins

from multiview import file


class RecordingContext:

    def __init__(self, recording):
        self.recording = recording
        self.reader = None

    def compute_hash(self):
        return filehash(self.recording.url)

    def update_hash(self):
        self.recording.hash = self.compute_hash()

    def get_reader(self):
        if not self.reader:
            self.reader = imageio.get_reader(self.recording.url)

        return self.reader

    def get_frame(self, index):
        return self.get_reader().get_data(index)

    def get_length(self):
        return self.get_reader().get_length()

    def get_size(self):
        return self.get_reader().get_data(0).shape
