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
        self.label.setBackgroundRole(QPalette.Base)
        self.label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.scroll = QScrollArea()
        self.scroll.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.scroll.setWidget(self.label)

        self.setCentralWidget(self.scroll)

        # Initialize Toolbar
        self.toolbar = QToolBar()
        self.toolbar.addAction(self.style().standardIcon(QStyle.SP_TitleBarNormalButton), "Dock/Undock", self.on_toggle_dock)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Initialize MDI Subwindow (if docked)
        self.subwindow = QMdiSubWindow()
        self.subwindow.setWindowTitle(id)
        self.subwindow.setWidget(self)
        self.docked = True

        # Member variables
        self.frame = None
        self.image = None
        self.pixmap = None

    def update_frame(self):
        self.frame = self.context.get_frame(self.id)

        if self.frame is not None:
            # 'Detect' image format
            format = QImage.Format_Indexed8
            if self.frame.ndim > 2 and self.frame.shape[2] > 1:
                format = QImage.Format_RGB888

            # 'Convert' image to displayable pixmap
            self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], format)
            self.pixmap = QPixmap.fromImage(self.image)
            self.label.setPixmap(self.pixmap)
            self.label.adjustSize()

    # Toolbar callbacks

    def on_toggle_dock(self):
        if self.docked:
            self.subwindow.setWidget(None)
            self.subwindow.hide()

            self.setParent(None)
            self.show()

            self.docked = False
        else:
            self.subwindow.setWidget(self)
            self.subwindow.show()

            self.docked = True
