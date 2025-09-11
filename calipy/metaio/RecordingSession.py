# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import logging
from pathlib import Path
import hashlib
import yaml

from svidreader import filtergraph


logger = logging.getLogger(__name__)


def get_offset_from_reader(vid_reader):
    header = vid_reader.get_meta_data()

    if 'sensor' in header:
        return tuple(header['sensor']['offset'])
    elif 'offset' in header:
        return tuple(header['offset'])
    else:
        logger.log(logging.INFO, "Setting offset to 0!")
        return tuple([0, 0])


def filehash(url):
    block_size = 65536
    hash_fun = hashlib.md5()
    count = 0

    with open(url, 'rb') as f:
        buffer = f.read(block_size)
        while len(buffer) > 0 and (count < 100):
            hash_fun.update(buffer)
            buffer = f.read(block_size)
            count += 1
    return hash_fun.hexdigest()


class Recording(yaml.YAMLObject):

    def __init__(self, url, rec_hash=None, pipeline=None):
        self.url = url
        self.rec_name = Path(url).stem
        self.pipeline = pipeline
        self.hash = rec_hash
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
        self.offset = get_offset_from_reader(reader)
        return reader

    def _compute_hash(self):
        """" Compute hash of the file behind the current url """
        return filehash(self.url)

    def get_hash(self):
        """' Get hash of the file or compute it if unknown """
        if self.hash is None:
            self.hash = self._compute_hash()

        return self.hash

    def check_hash(self):
        """" Check if hash is valid. If hash is unknown, hash is computed twice and compared """
        return self.get_hash() == self._compute_hash()

    def get_sensor_offset(self):
        if self.offset is None:
            # this is a bit circular, find a better way.
            self.offset = get_offset_from_reader(self.init_reader())
        return self.offset


class Session(yaml.YAMLObject):

    def __init__(self, session_id: str):
        self.id = session_id
        self.comment = ""
        self.recordings = {}
        self.fps = None

    def add_recording(self, id_str, url, rec_hash, pipeline=None):
        self.recordings[id_str] = Recording(url, rec_hash, pipeline)
        return self.recordings[id_str]

    def remove_recording(self, rec_id):
        del self.recordings[rec_id]
