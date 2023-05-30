# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt, QResizeEvent, QStyle, QSizePolicy
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QImage, QPixmap, QPalette
from PyQt5.QtWidgets import QMainWindow, QToolBar, QFrame, QGraphicsView, QLabel, QComboBox
from PyQt5.QtWidgets import QGraphicsScene,  QGraphicsPixmapItem
from PyQt5.QtWidgets import QMdiSubWindow, QFileDialog

import imageio


class FrameWindow(QMainWindow):

    def __init__(self, context, id):
        self.context = context
        self.id = id

        # Initialize widget
        super().__init__()
        self.setWindowTitle(id)

        self.viewer = QGraphicsView(self)
        self.viewer.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.viewer.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 100, 30)))
        self.setCentralWidget(self.viewer)

        # Initialize Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        self.action_undock = self.toolbar.addAction("Dock/Undock", self.on_toggle_dock)
        self.action_undock.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.action_undock.setCheckable(True)

        self.action_scale = self.toolbar.addAction("Autoscale", self.on_toggle_scale)
        self.action_scale.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.action_scale.setCheckable(True)

        self.toolbar.addAction("Save", self.on_save)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Initialize MDI Subwindow (if docked)
        self.subwindow = QMdiSubWindow()
        self.subwindow.setWindowTitle(id)
        self.subwindow.setWidget(self)

        # Member variables
        self.frame = None
        self.image = None
        self.pixmap = None

        self.resize = False

        self._scene = QGraphicsScene(self.viewer)
        self._pxi = QGraphicsPixmapItem()
        self._scene.addItem(self._pxi)
        self.viewer.setScene(self._scene)

    def update_frame(self):
        """ Reload current frame from context and display it """
        self.frame = self.context.get_frame(self.id)

        if self.frame is not None:
            bytes_per_line = int(self.frame.nbytes / self.frame.shape[0])

            # 'Detect' image format
            format = QImage.Format_Indexed8
            if self.frame.ndim > 2 and self.frame.shape[2] > 1:
                format = QImage.Format_RGB888

            # 'Convert' image to displayable pixmap
            self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], bytes_per_line, format)
            self.pixmap = QPixmap.fromImage(self.image)

            self.update_pixmap()

    def update_pixmap(self):
        if self.pixmap:
            self._pxi.setPixmap(self.pixmap)

            rect = QtCore.QRectF(self._pxi.pixmap().rect())
            self.viewer.setSceneRect(rect)

            unity = self.viewer.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self.viewer.scale(1 / unity.width(), 1 / unity.height())

            view_rect = self.viewer.viewport().rect()
            scene_rect = self.viewer.transform().mapRect(rect)

            if self.resize:
                factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())
            else:
                factor = 2 * max(view_rect.width() / scene_rect.width(),
                                 view_rect.height() / scene_rect.height())
            self.viewer.scale(factor, factor)

    # Qt overrides

    def show(self):
        if self.action_undock.isChecked():
            super().show()
        else:
            self.subwindow.show()

    def hide(self):
        if self.action_undock.isChecked():
            super().hide()
        else:
            self.subwindow.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap()

    # Toolbar callbacks

    def on_toggle_dock(self):
        if self.action_undock.isChecked():
            self.subwindow.setWidget(None)
            self.subwindow.hide()

            self.setParent(None)
            self.show()
        else:
            self.subwindow.setWidget(self)
            self.subwindow.show()

    def on_toggle_scale(self):
        self.resize = self.action_scale.isChecked()
        self.update_pixmap()

    def on_save(self):
        file = QFileDialog.getSaveFileName(self, "Save Frame", "", "PNG Image (*.png)")[0]

        if file:
            file += '.png' if not file.endswith('.png') else ''
            imageio.imwrite(file, self.frame)
