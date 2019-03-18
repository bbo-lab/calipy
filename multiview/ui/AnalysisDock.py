# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from PyQt5.Qt import Qt, QFont

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QComboBox


from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem, QPushButton, QMenu
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

        # Setup layout
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.combo_algorithm)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_detect)
        button_layout.addWidget(self.button_calibrate)

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.widget.setLayout(main_layout)
        self.setWidget(self.widget)

    def on_detect(self):
        dialog = QProgressDialog("Detection in progress, please wait.", "Cancel", 0, 00, self)
        dialog.setWindowModality(Qt.WindowModal)

        self.context.run_algorithm(self.combo_algorithm.currentIndex())

        dialog.cancel()

    def on_calibrate(self):
        pass

