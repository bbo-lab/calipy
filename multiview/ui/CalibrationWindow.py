# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from multiview import ui

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QMainWindow, QMdiArea, QFileDialog, QMessageBox


class CalibrationWindow(QMainWindow):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__()
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.subwindows = {}

        # Setup menu bar
        session_menu = self.menuBar().addMenu("&File")
        session_menu.addAction("&Open...", self.on_system_open)
        session_menu.addAction("&Save...", self.on_system_save)
        session_menu.addSeparator()
        session_menu.addAction("&Clear", self.on_system_clear)
        session_menu.addSeparator()
        session_menu.addAction("&Quit", self.on_quit)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction("&Tile", self.mdi.tileSubWindows)
        view_menu.addAction("&Cascade", self.mdi.cascadeSubWindows)

        result_menu = self.menuBar().addMenu("&Result")
        result_menu.addAction("&Load...", self.on_result_load)
        result_menu.addAction("&Save...", self.on_result_save)

        # Setup docks
        self.dock_session = ui.CameraSystemDock(context)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_session)

        self.dock_time = ui.TimeControlDock(context)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_time)

        self.dock_analysis = ui.AnalysisDock(context)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_analysis)

    def sync_subwindows_cameras(self):
        """ Create or destroy windows based on available cameras """
        win_ids = list(self.subwindows.keys())
        cam_ids = [cam.id for cam in self.context.get_cameras()]

        # Close obsolete views
        for id in win_ids:
            if id not in cam_ids:
                self.subwindows[id].close()
                del self.subwindows[id]

        # Open missing windows
        for id in cam_ids:
            if id not in win_ids:
                window = ui.FrameWindow(self.context, id)
                self.mdi.addSubWindow(window)
                self.subwindows[id] = window

        # Update time control
        self.dock_time.update_slider()

        self.update_subwindows()

    def sync_subwindows_sources(self):
        """" Show or hide subwindows based on available data """
        for id, win in self.subwindows.items():
            if self.context.get_frame(id) is None:
                win.hide()
            else:
                win.show()

        self.dock_time.update_slider()

        self.update_subwindows()

    def update_subwindows(self):
        """ Update current frame on all subwindows """
        for sub in self.subwindows.values():
            sub.update_frame()

    # File Menu Callbacks

    def on_system_open(self):
        """ MenuBar > Camera System > Open ..."""
        file = QFileDialog.getOpenFileName(self, "Open Camera System Config", "", "Session File (*.system.yml)")[0]

        if file:
            self.context.load(file)
            self.dock_session.update_all()

            self.sync_subwindows_cameras()
            self.sync_subwindows_sources()

    def on_system_save(self):
        """ MenuBar > Camera System > Save ..."""
        file = QFileDialog.getSaveFileName(self, "Save Camera System Config", "", "Session File (*.system.yml)")[0]

        if file:
            self.context.save(file)

    def on_system_clear(self):
        """ MenuiBar > Camera System > Clear """
        if QMessageBox.question(self, "Clear Session?", "All unsaved changes will be lost!"):
            self.context.clear()
            self.dock_session.update_all()

            self.sync_subwindows_cameras()

    def on_quit(self):
        """ MenuiBar > Camera System > Quit """
        self.close()

    # Result Menu Callbacks

    def on_result_load(self):
        """ MenuBar > Result > Load """
        file = QFileDialog.getOpenFileName(self, "Load Algorithm Result", "", "Result File (*.result.pickle)")[0]

        if file:
            self.context.load_result(file)

    def on_result_save(self):
        """ MenuBar > Result > Save """
        file = QFileDialog.getSaveFileName(self, "Save Algorithm Result", "", "Result File (*.result.pickle)")[0]

        if file:
            self.context.save_result(file)

