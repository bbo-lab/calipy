# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox, QPushButton
from PyQt5.QtWidgets import QProgressDialog, QMessageBox

from pyqtgraph.parametertree import Parameter, ParameterTree

class CalibrationDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Calibration")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget()

        # Algorithm selection
        self.combo_model = QComboBox(self)
        self.combo_model.addItems(self.context.get_model_names())
        self.combo_model.currentIndexChanged.connect(self.on_model_change)

        # Buttons
        self.button_camera_calibrate = QPushButton("Calibrate Cameras")
        self.button_camera_calibrate.clicked.connect(self.on_camera_calibrate)

        self.button_system_calibrate = QPushButton("Calibrate System")
        self.button_system_calibrate.clicked.connect(self.on_system_calibrate)

        # Result stats
        self.table_calibrations = QTableWidget(0, 4, self)
        self.table_calibrations.setHorizontalHeaderLabels(["Source", "Avg. Error", "Inputs", "Sys. Errors (max./med.)"])

        # Display selection
        self.combo_display_calib = QComboBox(self)
        self.combo_display_calib.addItems(["Single Calibration",
                                            "System Calibration"])
        self.combo_display_calib.currentIndexChanged.connect(self.on_display_calib_change)

        # Setup layout
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.combo_model)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_camera_calibrate)
        button_layout.addWidget(self.button_system_calibrate)
        main_layout.addLayout(button_layout)

        main_layout.addWidget(self.table_calibrations)

        main_layout.addWidget(self.combo_display_calib)

        self.widget.setLayout(main_layout)
        self.setWidget(self.widget)

    def set_calibration_table(self, row, column, value):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled)
        self.table_calibrations.setItem(row, column, item)

    def update_result(self):
        stats = self.context.get_calibration_stats()
        self.table_calibrations.setRowCount(len(stats))

        for index, (id, result) in enumerate(stats.items()):
            self.set_calibration_table(index, 0, id)
            self.set_calibration_table(index, 1, "{:.2f}".format(result['error']))
            self.set_calibration_table(index, 2, "{detections:d} / {usable:d} / {estimations:d}".format(**result))
            if 'system_errors' in result:
                self.set_calibration_table(index, 3, "{:.2f} / {:.2f}".format(*result['system_errors']))

    # Button Callbacks

    def on_model_change(self):
        self.context.select_model(self.combo_model.currentIndex())

        self.update_result()

    def on_display_calib_change(self):
        self.context.select_display_calib(self.combo_display_calib.currentIndex())

        self.parent().update_subwindows()

    def on_camera_calibrate(self):
        dialog = QProgressDialog("Camera calibration in progress...", "Cancel calibration", 0, 0, self)
        dialog.setMinimumDuration(0)
        dialog.setWindowModality(Qt.WindowModal)

        try:
            self.context.calibrate_cameras(dialog)
        except Exception as e:
            QMessageBox.critical(self, "Camera Calibration Error:", str(e))

        dialog.reset()
        self.update_result()

        self.parent().update_subwindows()

    def on_system_calibrate(self):
        dialog = QProgressDialog("System calibration in progress...", "Cancel calibration", 0, 0, self)
        dialog.setMinimumDuration(0)
        dialog.setWindowModality(Qt.WindowModal)

        try:
            self.context.calibrate_system(dialog)
        except Exception as e:
            QMessageBox.critical(self, "System Calibration Error:", str(e))

        dialog.reset()
        self.update_result()

        self.parent().update_subwindows()
