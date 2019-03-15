# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import yaml

import imageio
import multiview.imageio # Load imageio plugins

from .utils import filehash


class Recording(yaml.YAMLObject):

    def __init__(self, url):
        self.url = url
        self.hash = filehash(url)

    def get_reader(self):
        return imageio.get_reader(self.url)


class Session(yaml.YAMLObject):

    def __init__(self):
        self.description = ""
        self.comment = ""
        self.recordings = {}
        self.sync = None

    def add_recording(self, id, url):
        self.recordings[id] = Recording(url)

    def remove_recording(self, id):
        del self.recordings[id]
