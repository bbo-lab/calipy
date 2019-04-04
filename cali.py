#!/usr/bin/env python3

# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

from PyQt5.QtWidgets import QApplication

import multiview.core as mvc
import multiview.ui as mvui

if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationDisplayName("CaliPy")

    context = mvc.CalibrationContext()

    gui = mvui.MainWindow(context)
    gui.resize(QApplication.primaryScreen().availableSize() * 3 / 5)
    gui.show()

    app.exec_()

