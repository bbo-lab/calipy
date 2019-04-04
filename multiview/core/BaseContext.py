# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, Any

from .RecordingContext import RecordingContext

from multiview import file


class BaseContext:
    """ Controller-style class to handle camera systems management """
    recordings: Dict[str, RecordingContext]

    def __init__(self):
        self.system = file.CameraSystem()
        self.session = None
        self.frame_index = 0

        self.recordings = {}

        self.subset = None

    # Camera System

    def load(self, path):
        """ Load current camera system from file """
        self.system = file.CameraSystem.load(path)

        if self.system.sessions:
            self.select_session(0)

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

        # Close open files if necessary
        if id in self.recordings:
            del self.recordings[id]

        self.system.remove_camera(id)

    # Sessions

    def get_session(self, index):
        """ Get session of specific index """
        return self.system.sessions[index]

    def get_sessions(self):
        """ Get all available sessions """
        return self.system.sessions

    def add_session(self):
        """ Add a new session """
        self.recordings.clear()

        self.session = self.system.add_session()

    def select_session(self, index):
        """ Select session by index """
        self.recordings.clear()

        self.session = self.system.sessions[index]

        for id, rec in self.session.recordings.items():
            self.recordings[id] = RecordingContext(rec)

    def remove_session(self, index):
        """ Remove session by index """
        if self.session == self.system.sessions[index]:
            self.recordings.clear()
            self.session = None

        self.system.remove_session(index)

    # Recordings

    def add_recording(self, id, path):
        """ Add recording to current session """
        if not self.session:
            return None

        if id in self.recordings:
            del self.recordings[id]

        rec = self.session.add_recording(id, path, None)

        self.recordings[id] = RecordingContext(rec)

    def get_current_source_ids(self):
        """ Return current camera to source identifier map """
        sources = {}
        for cam in self.get_cameras():
            rec = self.recordings.get(cam.id, None)

            if rec:
                sources[cam.id] = rec.get_source_id()

    def get_all_source_ids(self):
        """" Return a map containing all camera to source maps """
        result = []
        for session in self.system.sessions:
            sources = {}

            for cam_id, rec in session.recordings.items():
                sources[cam_id] = RecordingContext(rec).get_source_id()

            if sources:
                result.append(sources)

        return result

    def set_recording_filter(self, id, filter):
        self.recordings[id].set_filter(filter)

    def get_recording_filter(self, id):
        return self.recordings[id].get_filter()

    def remove_recording(self, id):
        """ Remove recording from current session """
        if not self.session:
            return

        if id in self.recordings:
            del self.recordings[id]

        self.session.remove_recording(id)

    # Frames

    def get_length(self):
        """ Get frame count of current session or subset """
        if not self.session or not self.recordings:
            return 0

        # Find minimum length
        return min([rec.get_length() for rec in self.recordings.values()])

    def set_current_frame(self, index):
        """ Set current frame index, based on current subset setting """

        self.frame_index = index

    def get_current_frame(self):
        """ Get current frame index """
        return self.frame_index

    def get_frame(self, id):
        """ Get current frame by camera id"""
        # Abort if there is no recording for camera
        if id not in self.recordings:
            return None

        # Return frame at current index
        return self.recordings[id].get_frame(self.frame_index)

    def get_source_id(self, id):
        if id not in self.recordings:
            return None

        return self.recordings[id].get_source_id()

    # Index subsets

    def get_available_subsets(self):
        """ Return available subsets of frames """
        return {"All": None}
