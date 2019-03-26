#!/usr/bin/env python3

# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

from PyQt5.QtWidgets import QApplication

import multiview.core as mv
import multiview.ui as mvui

if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationDisplayName("MultiView Calibrator")

    context = mv.CalibrationContext()

    gui = mvui.CalibrationWindow(context)
    gui.resize(QApplication.primaryScreen().availableSize() * 3 / 5)
    gui.show()

    app.exec_()

