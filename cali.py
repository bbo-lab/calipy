#!/usr/bin/env python3

# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

from PyQt5.QtWidgets import QApplication

from calipy import ui, core

if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationDisplayName("CaliPy")

    context = core.CalibrationContext()

    gui = ui.MainWindow(context)
    gui.resize(QApplication.primaryScreen().availableSize() * 3 / 5)
    gui.show()

    app.exec_()

