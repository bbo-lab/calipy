# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from PyQt5.Qt import Qt, QFont

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox, QPushButton

from PyQt5.QtWidgets import QProgressDialog, QFileDialog, QInputDialog, QMessageBox, QLineEdit


class AnalysisDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Available analyses")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget()

        # Algorithm selection
        self.combo_algorithm = QComboBox(self)
        self.combo_algorithm.addItems(self.context.get_algorithm_names())

        # Buttons
        self.button_detect = QPushButton("Detect")
        self.button_detect.clicked.connect(self.on_detect)
        self.button_calibrate = QPushButton("Calibrate")
        self.button_calibrate.clicked.connect(self.on_calibrate)

        # Result stats
        self.table_detections = QTableWidget(0, 3, self)
        self.table_detections.setHorizontalHeaderLabels(["Source", "Patterns", "Markers (Avg.)"])

        self.table_calibrations = QTableWidget(0, 2, self)
        self.table_calibrations.setHorizontalHeaderLabels(["Source", "Avg. Error"])

        # Setup layout
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.combo_algorithm)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_detect)
        button_layout.addWidget(self.button_calibrate)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table_detections)
        main_layout.addStretch()
        main_layout.addWidget(self.table_calibrations)

        self.widget.setLayout(main_layout)
        self.setWidget(self.widget)

    def set_result_table(self, row, column, value):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled)
        self.table_detections.setItem(row, column, item)

    def set_calibration_table(self, row, column, value):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled)
        self.table_calibrations.setItem(row, column, item)

    def update_result(self):
        stats = self.context.get_detection_stats()
        self.table_detections.setRowCount(len(stats))

        for index, (id, stat) in enumerate(stats.items()):
            self.set_result_table(index, 0, id)
            self.set_result_table(index, 1, str(stat[0]))
            self.set_result_table(index, 2, "{:.2f}".format(stat[1] / stat[0]))

        errors = self.context.get_calibration_errors()
        self.table_calibrations.setRowCount(len(errors))

        for index, (id, err) in enumerate(errors.items()):
            self.set_calibration_table(index, 0, id)
            self.set_calibration_table(index, 1, "{:.2f}".format(err))

    # Button Callbacks

    def on_detect(self):
        dialog = QProgressDialog("Detection in progress...", "Cancel detection", 0, 0, self)
        dialog.setWindowModality(Qt.WindowModal)

        self.context.run_algorithm(self.combo_algorithm.currentIndex(), dialog)

        dialog.reset()
        self.update_result()

    def on_calibrate(self):
        dialog = QProgressDialog("Calibration in progress...", "Cancel calibration", 0, 0, self)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setMinimumDuration(1)

        self.context.calibrate_cameras(self.combo_algorithm.currentIndex(), dialog)

        dialog.reset()
        self.update_result()


