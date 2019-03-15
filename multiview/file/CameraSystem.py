import yaml

from .RecordingSession import Session


class Camera(yaml.YAMLObject):

    def __init__(self, id):
        self.id = id
        self.description = ""
        self.comment = ""


class CameraSystem(yaml.YAMLObject):

    @staticmethod
    def load(file):
        with open(file, 'r') as f:
            return yaml.load(f)

    def save(self, file):
        with open(file, 'w') as f:
            f.write(yaml.dump(self))

    def __init__(self):
        # List of all camera identifiers of system
        self.cameras = []
        # List of all recording sessions
        self.sessions = []

    def add_camera(self, id):
        self.cameras.append(Camera(id))

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
