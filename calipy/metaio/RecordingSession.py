# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import yaml


class Recording(yaml.YAMLObject):

    def __init__(self, url, hash):
        self.url = url
        self.hash = hash
        self.filter = None


class Session(yaml.YAMLObject):

    def __init__(self):
        self.description = ""
        self.comment = ""
        self.recordings = {}
        self.sync = None

    def add_recording(self, id, url, hash):
        self.recordings[id] = Recording(url, hash)
        return self.recordings[id]

    def remove_recording(self, id):
        del self.recordings[id]
