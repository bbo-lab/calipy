# (c) 2019 Florian Franzen <Florian.Franzen@gmail.com>
# SPDX-License-Identifier: MPL-2.0

from math import isinf

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QSlider, QComboBox, QSpinBox, QLabel


class TimelineDock(QDockWidget):

    def __init__(self, context):
        self.context = context
        self.current_subset = None
        self.subsets = context.get_available_subsets()

        # Set up widget
        super().__init__("Timeline")
        self.setFeatures(self.NoDockWidgetFeatures)
        self.widget = QWidget(self)
        self.setWidget(self.widget)

        # Init time slider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setRange(0, 0)
        self.slider.valueChanged.connect(self.on_index_change)

        # Init label
        self.label_left = QLabel("0")
        self.label_right = QLabel("0")

        # Init center combo box
        self.box_subset = QComboBox()
        self.box_subset.currentIndexChanged.connect(self.on_subset_change)

        # Init center spin box
        self.box_current = QSpinBox()
        self.box_current.setRange(0, 0)
        self.box_current.valueChanged.connect(self.on_index_change)

        self.label_current = QLabel("")

        # Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.slider)

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.label_left)
        label_layout.addStretch()
        label_layout.addWidget(self.box_subset)
        label_layout.addWidget(self.box_current)
        label_layout.addWidget(self.label_current)
        label_layout.addStretch()
        label_layout.addWidget(self.label_right)

        main_layout.addLayout(label_layout)

        self.widget.setLayout(main_layout)

    def update_slider(self):
        """Update slider based on current document state"""
        if self.current_subset is None:
            maximum = self.context.get_length() - 1
        else:
            maximum = len(self.current_subset)

        if isinf(maximum):
            maximum = -1

        # FIXME: If current slider value is larger than maximum, current frame index will be overwrite by maximum,
        # because next line will trigger valueChanged.

        self.slider.setRange(0, maximum)
        self.box_current.setRange(0, maximum)
        self.label_right.setText("{:d}".format(maximum))

        index = self.context.get_current_frame()

        if self.current_subset is not None:
            index = self.current_subset.index(index)

        self.update_index(index)

    def update_index(self, value):
        """ Update current frame labels in center """
        self.slider.setValue(value)
        self.box_current.setValue(value)

        if self.current_subset is None:
            self.label_current.setText("")
        else:
            self.label_current.setText("{:d}".format(self.current_subset[value]))

    def update_subsets(self):
        """Update available frame subsets"""
        self.subsets = self.context.get_available_subsets()
        self.box_subset.clear()
        self.box_subset.addItems(list(self.subsets.keys()))

    # UI callbacks

    def on_index_change(self, value : int):
        # Sync center ui
        self.update_index(value)

        # Remap index if subset is set
        if self.current_subset is not None:
            value = self.current_subset[value]

        self.context.set_current_frame(value)

        # Update frame views
        self.parent().update_subwindows()

    def on_subset_change(self, value):
        # Ignore empty selection
        if value < 0:
            return

        sub_id = self.box_subset.currentText()
        self.current_subset = self.subsets[sub_id]

        # Map indices between subsets
        if self.current_subset is not None:
            index = self.context.get_current_frame()

            if index in self.current_subset:
                index = self.current_subset.index(index)
            else:
                self.context.set_current_frame(self.current_subset[0])
                index = 0

            self.update_index(index)

        self.update_slider()
