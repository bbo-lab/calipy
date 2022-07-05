# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import hashlib


# TODO: Encode as multihash
def filehash(url):
    block_size = 65536
    hash_fun = hashlib.md5()

    with open(url, 'rb') as f:
        buffer = f.read(block_size)
        while len(buffer) > 0:
            hash_fun.update(buffer)
            buffer = f.read(block_size)

    return hash_fun.hexdigest()
