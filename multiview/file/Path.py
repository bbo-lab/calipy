import os.path

class Path():
    EXCEPTION_SUFFIXES = ['.blend', '.obj', '.osg']

    def __init__(self, url):


        # Expand ~ symbol to path
        url = os.path.expanduser(url)

        self._path, file_name = os.path.split(url)

        # Check exception list for files with only one dot in ending
        n_dots = 2
        for suffix in self.EXCEPTION_SUFFIXES:
            if file_name[-len(suffix):] == suffix:
                n_dots = 1

        self._prefix_file = ".".join(file_name.split('.')[:-n_dots])

        self._prefix_full = os.path.join(self._path, self._prefix_file)

    @classmethod
    def fromArgV(co, index):
        import sys
        return co(sys.argv[index])

    def ofFileType(self, suffix):
        return self._prefix_full + suffix

    def existsFileType(self, suffix):
        return os.path.exists(self.ofFileType(suffix))

    def ofCalZip(self):
        return self.ofFileType(".cal.zip")

    def existsCalZip(self):
        return self.existsFileType(".cal.zip")

    def ofCalNpz(self):
        return self.ofFileType(".cal.npz")

    def existsCalNpz(self):
        return self.existsFileType(".cal.npz")

    def ofRef2Npy(self):
        return self.ofFileType(".ref2.npy")

    def existsRef2Npy(self):
        return self.existsFileType(".ref2.npy")

    def ofRef3Npy(self):
        return self.ofFileType(".ref3.npy")

    def existsRef3Npy(self):
        return self.existsFileType(".ref3.npy")
