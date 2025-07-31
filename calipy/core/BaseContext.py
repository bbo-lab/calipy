# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1
import logging
from typing import Dict, Any

from calipy import metaio


logger = logging.getLogger(__name__)


class BaseContext:
    """ Controller-style class to handle camera systems management """
    vid_readers: Dict

    def __init__(self):
        self.system = metaio.CameraSystem()
        self.session = None
        self.frame_index = 0

        self.vid_readers = {}

        self.subset = None

    # Camera System

    def load(self, path):
        """ Load current camera system from file """
        self.system = metaio.CameraSystem.load(path)

        if self.system.sessions:
            self.select_session(0)

    def save(self, path):
        """ Save current camera system to file """
        self.system.save(path)

    def clear(self):
        """ Clear current state """
        self.__init__()

    def close(self):
        """ Close all open files """
        for reader in self.vid_readers.values():
            reader.close()

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
        if id in self.vid_readers:
            del self.vid_readers[id]

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
        self.vid_readers.clear()

        self.session = self.system.add_session()

    def select_session(self, index):
        """ Select session by index """
        self.vid_readers.clear()

        self.session = self.system.sessions[index]

        for id, rec in self.session.recordings.items():
            self.vid_readers[id] = rec.init_reader()

    def remove_session(self, index):
        """ Remove session by index """
        if self.session == self.system.sessions[index]:
            self.vid_readers.clear()
            self.session = None

        self.system.remove_session(index)

    # Recordings

    def add_recording(self, id_str, path, pipeline=None):
        """ Add recording to current session """
        if not self.session:
            return

        if id_str in self.vid_readers:
            del self.vid_readers[id_str]

        rec = self.session.add_recording(id_str, path, None, pipeline=pipeline)
        self.vid_readers[id_str] = rec.init_reader()

    def get_current_source_ids(self):
        """ Return current camera to source identifier map """
        sources = {}
        for cam in self.get_cameras():
            rec = self.session.recordings.get(cam.id, None)

            if rec:
                sources[cam.id] = rec.get_source_id()

        return sources

    def get_all_source_ids(self):
        """" Return a map containing all camera to source maps """
        result = []
        for session in self.system.sessions:
            sources = {}

            for cam_id, rec in session.recordings.items():
                sources[cam_id] = rec.get_source_id()

            if sources:
                result.append(sources)

        return result

    def remove_recording(self, id):
        """ Remove recording from current session """
        if not self.session:
            return

        if id in self.vid_readers:
            del self.vid_readers[id]

        self.session.remove_recording(id)

    # Frames

    def get_length(self):
        """ Get frame count of current session or subset """
        if not self.session or not self.vid_readers:
            return 0

        # Find minimum length
        return min([reader.n_frames for reader in self.vid_readers.values()])

    def get_fps(self):
        """ Get frames per second for the session """
        if not self.session or not self.vid_readers:
            return 0

        if self.session.fps is None:
            def most_common(lst):
                return max(set(lst), key=lst.count)

            fps_list = []
            for id, reader in self.vid_readers.items():
                fps = reader.get_meta_data().get('fps', None)
                if fps is None:
                    logger.log(logging.WARNING, f"Could not find 'fps' for the video: "
                                                f"{self.session.recordings[id].url}, returning 60")
                    fps = 60
                fps_list.append(fps)

            # Find most common fps
            self.session.fps = most_common(fps_list)

        return self.session.fps

    def set_current_frame(self, index):
        """ Set current frame index, based on current subset setting """

        self.frame_index = index

    def get_current_frame(self):
        """ Get current frame index """
        return self.frame_index

    def get_frame(self, id):
        """ Get current frame by camera id"""
        # Abort if there is no recording for camera
        if id not in self.vid_readers:
            return None

        # Return frame at current index
        return self.vid_readers[id].get_data(self.frame_index)

    def get_source_id(self, id):
        if id not in self.session.recordings:
            return None

        return self.session.recordings[id].get_source_id()

    # Index subsets

    def get_available_subsets(self):
        """ Return available subsets of frames """
        return {"All": None}
