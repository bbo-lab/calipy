# (c) 2019 MPI for Neurobiology of Behavior, Florian Franzen, Abhilash Cheekoti
# SPDX-License-Identifier: LGPL-2.1

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtWidgets import QWidget, QDockWidget, QVBoxLayout
from pyqtgraph.parametertree import ParameterTree, Parameter


class DetectionDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Setup widget
        super().__init__("Detection")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget()

        # Result stats
        self.table_detections = QTableWidget(0, 3, self)
        self.table_detections.setHorizontalHeaderLabels(["Camera", "# Det. Frames", "# Markers (Avg.)"])

        # Setup layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table_detections)

        self.widget.setLayout(main_layout)
        self.setWidget(self.widget)

    def set_result_table(self, row, column, value):
        item = QTableWidgetItem(value)
        item.setFlags(Qt.ItemIsEnabled)
        self.table_detections.setItem(row, column, item)

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
