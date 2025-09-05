# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import logging
from pathlib import Path

import yaml
from svidreader import filtergraph

from .utils import filehash

logger = logging.getLogger(__name__)


class Recording(yaml.YAMLObject):

    def __init__(self, url, hash=None, pipeline=None):
        self.url = url
        self.rec_name = Path(url).stem
        self.pipeline = pipeline
        self.hash = hash
        self.filter = None
        self.offset = None

    def init_reader(self):
        """"""
        logger.log(logging.INFO, f"Loading recording: {self.url}")
        reader = filtergraph.get_reader(self.url, cache=False, backend='iio')
        if self.pipeline is not None:
            logger.log(logging.INFO, f"The recording pipeline is {self.pipeline}")
            reader = filtergraph.create_filtergraph_from_string([reader],
                                                                pipeline=self.pipeline)['out']
        self.offset = self.get_offset_from_reader(reader)
        return reader

    @staticmethod
    def get_offset_from_reader(reader):
        header = reader.get_meta_data()
        # Add required headers that are not normally part of standard video formats but are required information
        # for a full calibration
        # TODO add option to supply this via options. Currently, compressed videos may lack this info
        if 'sensor' in header:
            return tuple(header['sensor']['offset'])
        elif 'offset' in header:
            return tuple(header['offset'])
        else:
            logger.log(logging.INFO, "Setting offset to 0!")
            return tuple([0, 0])

    def _compute_hash(self):
        """" Compute hash of file behind current url """
        return filehash(self.url)

    def get_hash(self):
        """' Get hash of file or compute it if unknown """
        if self.hash is None:
            self.hash = self._compute_hash()

        return self.hash

    def check_hash(self):
        """" Check if hash is valid. If hash is unknown, hash is computed twice and compared """
        return self.get_hash() == self._compute_hash()

    def get_source_id(self):
        """" Generate unique source identifier """
        suffix = ("+" + self.pipeline) if self.pipeline else ""
        return self.get_hash() + suffix

    def get_sensor_offset(self):
        if self.offset is None:
            # this is a bit circular, find a better way.
            self.offset = self.get_offset_from_reader(self.init_reader())
        return self.offset


class Session(yaml.YAMLObject):

    def __init__(self, description):
        self.description = description
        self.comment = ""
        self.recordings = {}
        self.fps = None

    def add_recording(self, id_str, url, hash, pipeline=None):
        self.recordings[id_str] = Recording(url, hash, pipeline)
        return self.recordings[id_str]

    def remove_recording(self, id):
        del self.recordings[id]
