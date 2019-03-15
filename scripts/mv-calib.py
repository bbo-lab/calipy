from PyQt5.QtWidgets import QApplication

import multiview.core as mv
import multiview.ui as mvui

if __name__ == "__main__":
    app = QApplication([])

    context = mv.CameraSystemContext()

    gui = mvui.CalibrationWindow(context)
    gui.show()

    app.exec_()

