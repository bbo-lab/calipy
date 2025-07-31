# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt, QStyle, QSizePolicy
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QToolBar, QFrame, QGraphicsView, QLabel, QComboBox
from PyQt5.QtWidgets import QGraphicsScene,  QGraphicsPixmapItem
from PyQt5.QtWidgets import QMdiSubWindow, QFileDialog

import numpy as np
import imageio


class FrameWindow(QMainWindow):

    def __init__(self, context, id_str: str):
        # Initialize widget
        super().__init__()
        self.context = context
        self.id = id_str
        self.setWindowTitle(id_str)

        self.viewer = Viewer()
        self.viewer.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 100, 30)))
        self.viewer.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.viewer.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.viewer.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.viewer.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.setCentralWidget(self.viewer)

        # Initialize Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        self.action_undock = self.toolbar.addAction("Dock/Undock", self.on_toggle_dock)
        self.action_undock.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.action_undock.setCheckable(True)

        self.action_scale = self.toolbar.addAction("Autoscale", self.on_toggle_scale)
        self.action_scale.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))

        self.toolbar.addAction("Save", self.on_save)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Initialize MDI Subwindow (if docked)
        self.subwindow = QMdiSubWindow()
        self.subwindow.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.subwindow.setWindowTitle(id_str)
        self.subwindow.setWidget(self)

        # Member variables
        self.frame = None
        self.image = None
        self.pixmap = None
        self.zoom = 0

        self._scene = QGraphicsScene(self.viewer)
        self._pxi = QGraphicsPixmapItem()
        self._scene.addItem(self._pxi)
        self.viewer.setScene(self._scene)
        # TODO: change to pyqtgraph

    def update_frame(self):
        """ Reload current frame from context and display it """
        self.frame = self.context.get_frame(self.id)

        if self.frame is not None:
            bytes_per_line = self.frame.nbytes // self.frame.shape[0]

            # 'Detect' image format
            format = QImage.Format_Indexed8
            if self.frame.ndim > 2 and self.frame.shape[2] > 1:
                format = QImage.Format_RGB888

            # 'Convert' image to displayable pixmap
            self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], bytes_per_line, format)
            self.pixmap = QPixmap.fromImage(self.image)

            self.update_pixmap()

    def update_pixmap(self, resize=False):
        if self.pixmap:
            self._pxi.setPixmap(self.pixmap)

            if resize:
                rect = QtCore.QRectF(self._pxi.pixmap().rect())
                self.viewer.setSceneRect(rect)
                view_rect = self.viewer.viewport().rect()
                scene_rect = self.viewer.transform().mapRect(rect)

                factor = min(view_rect.width() / scene_rect.width(),
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
        self.update_pixmap(resize=True)

    def on_save(self):
        file = QFileDialog.getSaveFileName(self, "Save Frame", "", "PNG Image (*.png)")[0]

        if file:
            file += '.png' if not file.endswith('.png') else ''
            imageio.imwrite(file, np.squeeze(self.frame))


class Viewer(QGraphicsView):

    def __init__(self):
        super().__init__()

    def wheelEvent(self, event):
        # TODO: The zoom is not perfect yet, should fix this later
        if self.parent().frame is None:
            return

        if event.angleDelta().y() > 0:
            factor = 1.25
            self.parent().zoom += 1
        else:
            factor = 0.8
            self.parent().zoom -= 1

        if self.parent().zoom > 0:
            self.scale(factor, factor)
        else:
            self.parent().update_pixmap(resize=True)
            self.parent().zoom = 0

