# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import yaml

from multiview.core.utils import filehash


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
