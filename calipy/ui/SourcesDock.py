# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt, QFont

from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QPushButton, QMenu
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox

import enum

from calipy.rawio import FILTERS


class SourceType(enum.IntEnum):
    Session = 1000
    Recording = 1001


class SourcesDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Sources")
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

    # Add button callbacks

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

    # Edit button callbacks

    def on_source_edit(self):
        item = self.tree.currentItem()

        if not item:
            QMessageBox.critical(self, "No item selected", "Please select a session or recording first.")
            return

        if item.type() == SourceType.Session:
            self.on_session_edit(item)
        elif item.type() == SourceType.Recording:
            self.on_recording_edit(item)

        self.update_sources()

    def on_session_edit(self, item):
        description, result = QInputDialog.getText(self, "Edit description", "Current description:")

        if result:
            self.context.get_session(item.data(0, Qt.UserRole)).description = description

    def on_recording_edit(self, item):
        available = ["None"] + list(FILTERS.keys())

        cam_id = item.text(0)
        filter = self.context.get_recording_filter(cam_id)
        selected = available.index(filter) if filter in available else 0

        print("{}: {}".format(selected, filter))

        filter, success = QInputDialog.getItem(self, "Edit filter", "Filter step before processing", available, selected, False)

        if success:
            if filter == "None":
                filter = None

            self.context.set_recording_filter(cam_id, filter)

            self.parent().update_subwindow(cam_id)

    # Remove button callback

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
