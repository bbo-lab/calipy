# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

import argparse

from PyQt5.QtWidgets import QApplication

from . import core, ui, VERSION


def main():
    """Run main GUI with supplied arguments"""

    parser = argparse.ArgumentParser(prog="CaliPy")

    # Positional arguments
    parser.add_argument("file", help="Path to file to open on start", nargs='?')

    # Flags and special functions
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)

    config = parser.parse_args()

    app = QApplication([])
    app.setApplicationDisplayName(parser.prog)

    context = core.CalibrationContext()

    gui = ui.MainWindow(context)
    gui.resize(QApplication.primaryScreen().availableSize() * 3 / 5)
    gui.show()

    if config.file:
        gui.open(config.file)

    app.exec_()
