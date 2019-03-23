# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from PyQt5.Qt import Qt, QResizeEvent, QStyle, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap, QPalette
from PyQt5.QtWidgets import QMainWindow, QToolBar, QScrollArea, QLabel
from PyQt5.QtWidgets import QMdiSubWindow


class FrameWindow(QMainWindow):

    def __init__(self, context, id):
        self.context = context
        self.id = id

        # Initialize widget
        super().__init__()
        self.setWindowTitle(id)

        self.label = QLabel("None")
        self.label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.scroll = QScrollArea()
        self.scroll.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.scroll.setWidget(self.label)
        self.scroll.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(self.scroll)

        # Initialize Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        self.undock_action = self.toolbar.addAction("Dock/Undock", self.on_toggle_dock)
        self.undock_action.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.undock_action.setCheckable(True)

        self.resize_action = self.toolbar.addAction("Autoscale", self.on_toggle_fit)
        self.resize_action.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.resize_action.setCheckable(True)

        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        # Initialize MDI Subwindow (if docked)
        self.subwindow = QMdiSubWindow()
        self.subwindow.setWindowTitle(id)
        self.subwindow.setWidget(self)

        # Member variables
        self.frame = None
        self.image = None
        self.pixmap = None

        self.resize = False

    def update_frame(self):
        """ Reload current frame from context and display it """
        self.frame = self.context.get_frame(self.id)

        if self.frame is not None:
            # 'Detect' image format
            format = QImage.Format_Indexed8
            if self.frame.ndim > 2 and self.frame.shape[2] > 1:
                format = QImage.Format_RGB888

            # 'Convert' image to displayable pixmap
            self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], format)
            self.pixmap = QPixmap.fromImage(self.image)

            self.update_label()

    def update_label(self):
        """ Rescale current pixmap to latest window size """
        if self.pixmap:
            if self.resize:
                viewport = self.scroll.viewport()
                self.label.setPixmap(self.pixmap.scaled(viewport.width(), viewport.height(), Qt.KeepAspectRatio))
            else:
                self.label.setPixmap(self.pixmap)

            self.label.adjustSize()

    # Qt overrides
    
    def show(self):
        if self.undock_action.isChecked():
            super().show()
        else:
            self.subwindow.show()

    def hide(self):
        if self.undock_action.isChecked():
            super().hide()
        else:
            self.subwindow.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_label()

    # Toolbar callbacks

    def on_toggle_dock(self):
        if self.undock_action.isChecked():
            self.subwindow.setWidget(None)
            self.subwindow.hide()

            self.setParent(None)
            self.show()
        else:
            self.subwindow.setWidget(self)
            self.subwindow.show()

    def on_toggle_fit(self):
        self.resize = self.resize_action.isChecked()
        self.update_label()
