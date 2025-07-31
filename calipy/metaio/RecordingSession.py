# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import yaml

from pathlib import Path


class Recording(yaml.YAMLObject):

    def __init__(self, url, hash, pipeline=None):
        self.url = url
        self.rec_name = Path(url).stem
        self.pipeline = pipeline
        self.hash = hash
        self.filter = None


class Session(yaml.YAMLObject):

    def __init__(self, description):
        self.description = description
        self.comment = ""
        self.recordings = {}
        self.sync = None
        self.fps = None

    def add_recording(self, id_str, url, hash, pipeline=None):
        self.recordings[id_str] = Recording(url, hash, pipeline)
        return self.recordings[id_str]

    def remove_recording(self, id):
        del self.recordings[id]
