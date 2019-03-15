# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import hashlib


def filehash(url):
    block_size = 65536
    hash_fun = hashlib.md5()

    with open(url, 'rb') as f:
        buffer = f.read(block_size)
        while len(buffer) > 0:
            hash_fun.update(buffer)
            buffer = f.read(block_size)

    return hash_fun.hexdigest()
