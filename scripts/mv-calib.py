# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com >
# SPDX-License-Identifier: MPL-2.0

from PyQt5.QtWidgets import QApplication

import multiview.core as mv
import multiview.ui as mvui

if __name__ == "__main__":
    app = QApplication([])

    context = mv.CalibrationContext()

    gui = mvui.CalibrationWindow(context)
    gui.show()

    app.exec_()

