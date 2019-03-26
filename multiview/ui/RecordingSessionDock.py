# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from PyQt5.Qt import Qt, QFont

from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QPushButton, QMenu
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QLineEdit

import enum


class SourceType(enum.IntEnum):
    Session = 1000
    Recording = 1001


class RecordingSessionDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Recordings")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget()
        self.setWidget(self.widget)

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
   
        layout_main.addWidget(self.tree)

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(self.button_source_add)
        layout_buttons.addWidget(self.button_source_edit)
        layout_buttons.addWidget(self.button_source_remove)

        layout_main.addLayout(layout_buttons)

        self.widget.setLayout(layout_main)

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

    # Source UI callbacks

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
