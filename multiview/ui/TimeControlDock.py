# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QSlider, QSpinBox, QLabel


class TimeControlDock(QDockWidget):

    def __init__(self, context):
        self.context = context

        # Set up widget
        super().__init__("Time Control")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget(self)
        self.setWidget(self.widget)

        # Init time slider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setRange(0, 0)
        self.slider.valueChanged.connect(self.on_change)

        # Init label
        self.label_left = QLabel("0")
        self.label_right = QLabel("0")

        self.box_current = QSpinBox()
        self.box_current.setRange(0, 0)
        self.box_current.valueChanged.connect(self.on_change)

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.slider)

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.label_left)
        label_layout.addStretch()
        label_layout.addWidget(self.box_current)
        label_layout.addStretch()
        label_layout.addWidget(self.label_right)

        main_layout.addLayout(label_layout)

        self.widget.setLayout(main_layout)

    def update_slider(self):
        """Update slider based on current document state"""
        max = self.context.get_length() - 1

        self.slider.setRange(0, max)
        self.box_current.setRange(0, max)
        self.label_right.setText("{:d}".format(max))

        self.slider.setValue(self.context.get_current_frame())
        self.slider.setValue(self.context.get_current_frame())

    def on_change(self, value : int):
        self.context.set_current_frame(value)

        self.slider.setValue(value)
        self.box_current.setValue(value)

        self.parent().update_subwindows()

