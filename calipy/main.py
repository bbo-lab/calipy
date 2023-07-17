# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

import argparse

from PyQt5.QtWidgets import QApplication

from . import core, ui, VERSION


def main():
    """Run main GUI with supplied arguments"""

    parser = argparse.ArgumentParser(prog="CaliPy")

    # Positional arguments
    parser.add_argument("--file", type=str, required=False, nargs=1, default=[None],
                        help="yml file (*.system.yml) path to open on start")
    parser.add_argument("--calibcam_file", type=str, required=False, nargs=1, default=[None],
                        help="npy file path generated with calibcam to open on start")
    parser.add_argument("--storage", type=str, required=False, nargs=1, default=[None],
                        help="path to bbo storage")

    config = parser.parse_args()

    app = QApplication([])
    app.setApplicationDisplayName(parser.prog)

    context = core.CalibrationContext()

    gui = ui.MainWindow(context)
    gui.resize(QApplication.primaryScreen().availableSize() * 4 / 5)
    gui.show()

    if config.file[0] is not None:
        gui.open(file=config.file[0], storage=config.storage[0])
        if config.calibcam_file[0] is not None:
            gui.on_result_load_npy(file=config.calibcam_file[0])

    app.exec_()
