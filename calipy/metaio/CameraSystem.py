# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import yaml

from .RecordingSession import Session


class Camera(yaml.YAMLObject):

    def __init__(self, id):
        self.id = id
        self.description = ""
        self.comment = ""


class CameraSystem(yaml.YAMLObject):

    @staticmethod
    def load(url):
        with open(url, 'r') as file:
            # ToDo: Do not specify type in yaml and switch to SafrLoader?
            return yaml.load(file, Loader=yaml.Loader)

    def save(self, url):
        with open(url, 'w') as file:
            yaml.dump(self, file)

    def __init__(self):
        # List of all camera identifiers of system
        self.cameras = []
        # List of all recording sessions
        self.sessions = []

    def add_camera(self, id):
        self.cameras.append(Camera(id))
        return self.cameras[-1]

    def get_camera(self, id):
        for cam in self.cameras:
            if cam.id == id:
                return cam
        return None

    def remove_camera(self, id):
        self.cameras = list(filter(lambda r: r.id != id, self.cameras))

    def add_session(self):
        self.sessions.append(Session())
        return self.sessions[-1]

    def remove_session(self, index):
        del self.sessions[index]
