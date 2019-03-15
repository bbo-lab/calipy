from PyQt5.Qt import Qt, QFont

from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QPushButton, QMenu
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QLineEdit

import enum


class SourceType(enum.IntEnum):
    Session = 1000
    Recording = 1001


class CameraSystemDock(QDockWidget):
    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Camera System")
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

        # Init session tree widget
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Name", "Details"])
        self.tree.itemDoubleClicked.connect(self.on_source_select)

        # Add session buttons
        self.button_source_add = QPushButton("Add...")
        menu_source_add = QMenu(self.button_source_add)
        menu_source_add.addAction("Session", self.on_session_add)
        menu_source_add.addAction("Recording", self.on_recording_add)
        self.button_source_add.setMenu(menu_source_add)

        self.button_source_edit = QPushButton("Edit")
        self.button_source_edit.clicked.connect(self.on_source_edit)

        self.button_source_remove = QPushButton("Remove")
        self.button_source_remove.clicked.connect(self.on_source_remove)

        # Layout everything
        layout_main = QVBoxLayout()

        layout_main.addWidget(QLabel("Current Cameras:"))
        layout_main.addWidget(self.list)

        layout_top = QHBoxLayout()
        layout_top.addWidget(self.button_camera_add)
        layout_top.addWidget(self.button_camera_edit)
        layout_top.addWidget(self.button_camera_remove)

        layout_main.addLayout(layout_top)

        layout_main.addWidget(QLabel("Current Sessions:"))
        layout_main.addWidget(self.tree)

        layout_bottom = QHBoxLayout()
        layout_bottom.addWidget(self.button_source_add)
        layout_bottom.addWidget(self.button_source_edit)
        layout_bottom.addWidget(self.button_source_remove)

        layout_main.addLayout(layout_bottom)

        self.widget.setLayout(layout_main)

    def update_cameras(self):
        self.list.clear()

        # Update list of cameras
        for cam in self.context.get_cameras():
            camera_item = QListWidgetItem("{} ({})".format(cam.id, cam.description), self.list)
            camera_item.setData(Qt.UserRole, cam.id)

    def update_sources(self):
        # Update source tree
        self.tree.clear()

        for index, session in enumerate(self.context.get_sessions()):
            session_item = QTreeWidgetItem(["Session {}".format(index), session.description], SourceType.Session)
            session_item.setData(0, Qt.UserRole, index)

            if session == self.context.session:
                session_item.setExpanded(True)
                font = QFont()
                font.setBold(True)
                session_item.setFont(0, font)

            for id, rec in session.recordings.items():
                recording_item = QTreeWidgetItem([id, rec.url], SourceType.Recording)
                recording_item.setData(0, Qt.UserRole, id)
                recording_item.setToolTip(1, rec.hash)

                session_item.addChild(recording_item)

            self.tree.addTopLevelItem(session_item)

    def update_all(self):
        self.update_cameras()
        self.update_sources()

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

        self.context.remove_camera(item.data(Qt.UserRole))
        self.update_all()

        self.parent().sync_subwindows_cameras()

    # Source callbacks

    def on_source_select(self, item, column):
        if item.type() == SourceType.Session:
            self.context.select_session(item.data(0, Qt.UserRole))
            self.update_sources()

            self.parent().sync_subwindows_sources()

    def on_session_add(self):
        self.context.add_session()
        self.update_sources()

        self.parent().sync_subwindows_sources()

    def on_recording_add(self):
        if not self.context.session:
            QMessageBox.critical(self, "No session selected", "Please select a session first.")
            return

        cameras = self.context.get_cameras()

        if not cameras:
            QMessageBox.critical(self, "No camera available", "Please add camera first.")
            return

        ids = [cam.id for cam in cameras]

        id, result = QInputDialog.getItem(self, "Chose camera of recording", "Please select camera:", ids, 0, False)

        if result:
            path = QFileDialog.getOpenFileName(
                self,
                "Open Recording",
                "",
                "Video File (*.mp4 *.ccv);;All files (*.*)"
            )[0]

            if path:
                self.context.add_recording(id, path)
                self.update_sources()

                self.parent().sync_subwindows_sources()

    def on_source_edit(self):
        item = self.tree.currentItem()

        if not item:
            QMessageBox.critical(self, "No item selected", "Please select a session or recording first.")
            return

        descr, result = QInputDialog.getText(self, "Edit description", "Current description:")

        # ToDo: Implement!
        if result:
            if item.type() == SourceType.Session:
                print(descr)
            elif item.type() == SourceType.Recording:
                print(descr)

            self.update_sources()

    def on_source_remove(self):
        item = self.tree.currentItem()

        if not item:
            QMessageBox.critical(self, "No item selected", "Please select a session or recording first.")
            return

        if item.type() == SourceType.Session:
            self.on_session_remove(item)
        elif item.type() == SourceType.Recording:
            self.on_recording_remove(item)

        self.update_sources()

        self.parent().sync_subwindows_sources()

    def on_session_remove(self, item):
        selection = QMessageBox.question(self, "Delete Session", "This will remove the selected session and its links.")

        if selection == QMessageBox.Yes:
            self.context.remove_session(item.data(0, Qt.UserRole))

    def on_recording_remove(self, item):
        selection = QMessageBox.question(self, "Delete Recording", "This will remove the selected link to the recording.")

        if selection == QMessageBox.Yes:
            self.context.remove_recording(item.text(0))
