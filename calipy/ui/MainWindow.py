# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from calipy import ui
import numpy as np
from pathlib import Path

from PyQt5.Qt import Qt, QIcon
from PyQt5.QtWidgets import QMainWindow, QMdiArea, QFileDialog, QMessageBox


class MainWindow(QMainWindow):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__()
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.subwindows = {}

        # Setup menu bar
        session_menu = self.menuBar().addMenu("&File")
        session_menu.addAction(QIcon.fromTheme("document-open"), "&Open...", self.on_system_open)
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
        result_menu.addAction("&Load .npy", self.on_result_load_npy)
        result_menu.addAction("&Save...", self.on_result_save)
        result_menu.addSeparator()
        result_menu.addAction("&Clear", self.on_result_clear)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("&About", self.on_about)

        # Setup docks
        self.dock_cameras = ui.CamerasDock(context)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_cameras)

        self.dock_sessions = ui.SourcesDock(context)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_sessions)

        self.dock_time = ui.TimelineDock(context)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_time)

        self.dock_detection = ui.DetectionDock(context)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_detection)

        self.dock_calibration = ui.CalibrationDock(context)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_calibration)

    def open(self, file):
        """Open specified system file in UI"""

        if file.endswith(".npy"):
            temp_npy = np.load(file, allow_pickle=True).item()
            rec_files = temp_npy['rec_file_names']
            self.context.add_session()
            for idx, rec in enumerate(rec_files):
                self.context.add_camera(str(idx))
                if Path(rec).exists():
                    self.context.add_recording(str(idx), rec)

        else:
            self.context.load(file)

        self.dock_cameras.update_cameras()
        self.dock_sessions.update_sources()
        self.dock_time.update_subsets()

        self.sync_subwindows_cameras()
        self.sync_subwindows_sources()

    def update_cameras(self):
        """ Helper to update UI on camera changes """
        self.dock_cameras.update_cameras()
        self.dock_sessions.update_sources()

        self.sync_subwindows_cameras()

    def sync_subwindows_cameras(self):
        """ Create or destroy windows based on available cameras """
        win_ids = list(self.subwindows.keys())
        cam_ids = [cam.id for cam in self.context.get_cameras()]

        # Close obsolete views
        for id in win_ids:
            if id not in cam_ids:
                self.subwindows[id].subwindow.close()
                del self.subwindows[id]

        # Open missing windows
        for id in cam_ids:
            if id not in win_ids:
                window = ui.FrameWindow(self.context, id)
                self.mdi.addSubWindow(window.subwindow)
                self.subwindows[id] = window

        # Update time control
        self.dock_time.update_slider()

        # Reload current frame
        self.update_subwindows()

    def sync_subwindows_sources(self):
        """" Show or hide subwindows based on available data """
        # Reset frame index if now invalid
        if self.context.get_current_frame() > self.context.get_length():
            self.context.set_current_frame(0)

        # Display windows based on available sources
        for id, win in self.subwindows.items():
            if self.context.get_frame(id) is None:
                win.hide()
            else:
                win.show()

        # Update timeline
        self.update_dock_time()

        # Reload subwindow
        self.update_subwindows()

        # Update list of detections and calibrations (e.g. on session select) TODO: Move somewhere better
        self.dock_detection.update_result()
        self.dock_calibration.update_result()

    def update_subwindows(self):
        """ Update current frame on all subwindows """
        for sub in self.subwindows.values():
            sub.update_frame()

    def update_subwindow(self, id):
        """ Update current frame on specific subwindow """
        if id in self.subwindows:
            self.subwindows[id].update_frame()

    def update_dock_time(self):
        """ Update the timeline dock """
        self.dock_time.update_slider()
        self.dock_time.update_subsets()

    # File Menu Callbacks

    def on_system_open(self):
        """ MenuBar > Camera System > Open ..."""
        file = QFileDialog.getOpenFileName(self, "Open Camera System Config", "", "Session File (*.system.yml);;"
                                                                                  "Calibcam File (*.npy)")[0]

        if file:
            self.open(file)

    def on_system_save(self):
        """ MenuBar > Camera System > Save ..."""
        file = QFileDialog.getSaveFileName(self, "Save Camera System Config", "", "Session File (*.system.yml)")[0]

        if file:
            self.context.save(file)

    def on_system_clear(self):
        """ MenuiBar > Camera System > Clear """
        if QMessageBox.question(self, "Clear Session?", "All unsaved changes will be lost!") == QMessageBox.Yes:
            self.context.clear()
            self.dock_cameras.update_cameras()
            self.dock_sessions.update_sources()

            self.dock_time.update_subsets()

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

            self.dock_detection.update_param_values()
            self.dock_detection.update_result()
            self.dock_calibration.update_result()
            self.dock_time.update_subsets()

            self.update_subwindows()

    def on_result_load_npy(self):
        """ MenuBar > Result > Load .npy """
        file = QFileDialog.getOpenFileName(self, "Load Calibcam Result", "", "Result File (*.npy)")[0]

        if file:
            self.context.load_result_npy(file)

            self.dock_detection.update_param_values()
            self.dock_detection.update_result()
            self.dock_calibration.combo_model.setCurrentIndex(self.context.model_index)
            self.dock_calibration.update_result()
            self.dock_time.update_subsets()

            self.update_subwindows()

    def on_result_save(self):
        """ MenuBar > Result > Save """
        file = QFileDialog.getSaveFileName(self, "Save Algorithm Result", "", "Result File (*.result.pickle)")[0]

        if file:
            self.context.save_result(file)

    def on_result_clear(self):
        """ MenuBar > Result > Clear """
        if QMessageBox.question(self, "Clear Results?", "All unsaved changes will be lost!") == QMessageBox.Yes:
            self.context.clear_result()

            self.dock_detection.update_result()
            self.dock_calibration.update_result()
            self.dock_time.update_subsets()

            self.update_subwindows()

    # Help menu

    def on_about(self):
        QMessageBox.about(self, "About",
                          "(c) 2019 Florian Franzen, Abhilash Cheekoti, MPI for Neurobiology of Behavior, Bonn\nLicensed under LGPL 2.1")
