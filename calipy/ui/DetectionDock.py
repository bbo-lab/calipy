# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox, QPushButton

from PyQt5.QtWidgets import QProgressDialog, QMessageBox

from pyqtgraph.parametertree import ParameterTree, Parameter


class DetectionDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Detection")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget()

        # Algorithm selection
        self.combo_detector = QComboBox(self)
        self.combo_detector.addItems(self.context.get_detector_names())
        self.combo_detector.currentIndexChanged.connect(self.on_detector_change)

        # Settings
        self.parameters = Parameter(name="Detector Settings", type="group")
        self.parameters.sigTreeStateChanged.connect(self.on_param_change)

        self.tree_params = ParameterTree()
        self.tree_params.setParameters(self.parameters, showTop=False)

        self.update_params()

        # Result stats
        self.table_detections = QTableWidget(0, 3, self)
        self.table_detections.setHorizontalHeaderLabels(["Source", "Patterns", "Markers (Avg.)"])

        # Setup layout
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.combo_detector)
        main_layout.addWidget(self.tree_params)
        main_layout.addWidget(self.table_detections)

        self.widget.setLayout(main_layout)
        self.setWidget(self.widget)

    def set_result_table(self, row, column, value):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled)
        self.table_detections.setItem(row, column, item)

    def update_params(self):
        self.parameters.clearChildren()
        self.parameters.addChildren(self.context.get_current_detector().PARAMS)

    def update_param_values(self):
        self.parameters.clearChildren()
        borad_params = self.context.get_current_board_params()
        detector = self.context.get_current_detector()

        detector.configure(borad_params)
        self.parameters.addChildren(detector.PARAMS)
        QMessageBox.information(self, "Detection Parameters Update:", "Board parameters updated")

    def update_result(self):
        stats = self.context.get_detection_stats()
        self.table_detections.setRowCount(len(stats))

        for index, (id, stat) in enumerate(stats.items()):
            self.set_result_table(index, 0, id)
            self.set_result_table(index, 1, str(stat[0]))
            if stat[0]:
                self.set_result_table(index, 2, "{:.2f}".format(stat[1] / stat[0]))
            else:
                self.set_result_table(index, 2, "-")

    # Button Callbacks

    def on_detector_change(self):
        self.context.select_detector(self.combo_detector.currentIndex())

        self.update_result()
        self.update_params()

    def on_param_change(self, _, changes):
        for param, change, data in changes:
            if change == "value":
                self.context.set_current_board_parameter(param.name(), data)
