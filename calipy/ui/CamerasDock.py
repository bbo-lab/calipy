# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt, QFont

from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QPushButton, QMenu
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QLineEdit

import enum


class SourceType(enum.IntEnum):
    Session = 1000
    Recording = 1001


class CamerasDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Cameras")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget()
        self.setWidget(self.widget)

        # Init list widget
        self.list = QListWidget(self)

        # Add camera list buttons
        self.button_camera_add = QPushButton("Add")
        self.button_camera_add.clicked.connect(self.on_camera_add)

        self.button_camera_edit = QPushButton("Edit")
        self.button_camera_edit.clicked.connect(self.on_camera_edit)

        self.button_camera_remove = QPushButton("Remove")
        self.button_camera_remove.clicked.connect(self.on_camera_remove)

        # Layout everything
        layout_main = QVBoxLayout()

        layout_main.addWidget(self.list)

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(self.button_camera_add)
        layout_buttons.addWidget(self.button_camera_edit)
        layout_buttons.addWidget(self.button_camera_remove)

        layout_main.addLayout(layout_buttons)

        self.widget.setLayout(layout_main)

    def update_cameras(self):
        self.list.clear()

        # Update list of cameras
        for cam in self.context.get_cameras():
            camera_item = QListWidgetItem("{} ({})".format(cam.id, cam.description), self.list)
            camera_item.setData(Qt.UserRole, cam.id)

    # Camera callbacks

    def on_camera_add(self):
        id, result = QInputDialog.getText(self, "Identifier required", "Please enter the cameras identifier (e.g. serial)")
        if result:
            self.context.add_camera(id)
            self.update_cameras()

            self.parent().sync_subwindows_cameras()

    def on_camera_edit(self):
        item = self.list.currentItem()

        if not item:
            QMessageBox.critical(self, "No camera selected", "Please select camera first and try again.")
            return

        camera = self.context.get_camera(item.data(Qt.UserRole))

        if not camera:
            QMessageBox.critical(self, "Unknown camera selected", "Internal error, selected camera is unknown.")

        description, result = QInputDialog.getText(self, "Edit Camera '{}'".format(id), "Description:", QLineEdit.Normal, camera.description)

        if result:
            camera.description = description
            item.setText("{} ({})".format(camera.id, camera.description))

    def on_camera_remove(self):
        item = self.list.currentItem()

        if not item:
            QMessageBox.critical(self, "No camera selected", "Please selected camera.")
            return

        selection = QMessageBox.question(self, "Delete camera", "This will remove the selected camera and all associated links.")

        if selection == QMessageBox.Yes:
            self.context.remove_camera(item.data(Qt.UserRole))

            self.parent().update_cameras()
