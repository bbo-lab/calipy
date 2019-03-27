# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox, QPushButton

from PyQt5.QtWidgets import QProgressDialog


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

        # Buttons
        self.button_detect = QPushButton("Run Detection")
        self.button_detect.clicked.connect(self.on_detect)

        self.button_config = QPushButton("Configuration...")
        self.button_config.clicked.connect(self.on_config)

        # Result stats
        self.table_detections = QTableWidget(0, 3, self)
        self.table_detections.setHorizontalHeaderLabels(["Source", "Patterns", "Markers (Avg.)"])

        # Setup layout
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.combo_detector)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_detect)
        button_layout.addWidget(self.button_config)
        main_layout.addLayout(button_layout)

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

    # Button Callbacks

    def on_detect(self):
        dialog = QProgressDialog("Detection in progress...", "Cancel detection", 0, 0, self)
        dialog.setWindowModality(Qt.WindowModal)

        self.context.run_detection(self.combo_detector.currentIndex(), dialog)

        dialog.reset()
        self.update_result()

    def on_config(self):
        pass
