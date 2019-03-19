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
        self.table_result = QTableWidget(0, 3, self)
        self.table_result.setHorizontalHeaderLabels(["Camera", "Patterns", "Markers (Avg.)"])

        # Setup layout
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.combo_algorithm)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_detect)
        button_layout.addWidget(self.button_calibrate)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table_result)
        main_layout.addStretch()

        self.widget.setLayout(main_layout)
        self.setWidget(self.widget)

    def update_result(self):
        stats = self.context.get_result_stats()
        self.table_result.setRowCount(len(stats))

        # Little helper function
        def set_table(table, row, column, value):
            item = QTableWidgetItem(value)
            item.setFlags(Qt.ItemIsEnabled)
            table.setItem(row, column, item)

        for index, (id, stat) in enumerate(stats.items()):
            set_table(self.table_result, index, 0, id)
            set_table(self.table_result, index, 1, str(stat[0]))
            set_table(self.table_result, index, 2, "{:.2f}".format(stat[1] / stat[0]))

    # Button Callbacks

    def on_detect(self):
        dialog = QProgressDialog("Detection in progress, please wait.", "Cancel", 0, 00, self)
        dialog.setWindowModality(Qt.WindowModal)

        self.context.run_algorithm(self.combo_algorithm.currentIndex())

        dialog.cancel()

        self.update_result()

    def on_calibrate(self):
        pass

