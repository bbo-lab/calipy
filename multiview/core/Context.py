# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from multiview import file


class CameraSystemContext:
    """ Controller-style class to handle camera systems management """

    def __init__(self):
        self.system = file.CameraSystem()
        self.session = None
        self.readers = {}
        self.frame_index = 0

    # Camera System

    def load(self, path):
        """ Load current camera system from file """
        self.system = file.CameraSystem.load(path)

        if self.system.sessions:
            self.session = self.system.sessions[0]

    def save(self, path):
        """ Save current camera system to file """
        self.system.save(path)

    def clear(self):
        """ Clear current state """
        self.__init__()

    # Cameras

    def get_camera(self, id):
        """ Get camera of specified identifier """
        return self.system.get_camera(id)

    def get_cameras(self):
        """ Get all available cameras """
        return self.system.cameras

    def add_camera(self, id):
        """ Add a new camera """
        self.system.add_camera(id)

    def remove_camera(self, id):
        """ Remove a camera by identifier """

        for session in self.system.sessions:
            if id in session.recordings:
                del session.recordings[id]

        if id in self.readers:
            del self.readers[id]

        self.system.remove_camera(id)

    # Sessions

    def get_sessions(self):
        """ Get all available sessions """
        return self.system.sessions

    def add_session(self):
        """ Add a new session """
        self.readers.clear()

        self.session = self.system.add_session()

    def select_session(self, index):
        """ Select session by index """
        self.readers.clear()

        self.session = self.system.sessions[index]

    def remove_session(self, index):
        """ Remove session by index """
        if self.session == self.system.sessions[index]:
            self.readers.clear()
            self.session = None

        self.system.remove_session(index)

    # Recordings

    def add_recording(self, id, path):
        """ Add recording to current session """
        if id in self.readers:
            del self.readers[id]

        self.session.add_recording(id, path)

    def remove_recording(self, id):
        """ Remove recording from current session """
        if id in self.readers:
            del self.readers[id]

        self.session.remove_recording(id)

    # Frames

    def get_length(self):
        """ Get frame count of current session """
        if not self.session or not self.session.recordings:
            return 0

        # Make sure all readers were initialized
        for id in self.session.recordings.keys():
            if id not in self.readers:
                self.readers[id] = self.session.recordings[id].get_reader()

        # Find minimum length
        length = min([reader.get_length() for reader in self.readers.values()])
        return length

    def set_current_frame(self, index):
        """ Set current frame index """
        self.frame_index = index

    def get_frame(self, id):
        """ Get current frame by camera id"""
        # Abort if there is no recording for camera
        if not self.session or id not in self.session.recordings:
            return None

        # Open file if not open yet
        if id not in self.readers:
            self.readers[id] = self.session.recordings[id].get_reader()

        # Return frame at current index
        return self.readers[id].get_data(self.frame_index)
