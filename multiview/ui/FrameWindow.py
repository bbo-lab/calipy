from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMdiSubWindow, QLabel


class FrameWindow(QMdiSubWindow):

    def __init__(self, context, id):
        super().__init__()
        self.setWindowTitle(id)

        self.context = context
        self.id = id

        self.label = QLabel("None", self)
        #self.label.setScaledContents(True)

        self.frame = None
        self.image = None

        self.setWidget(self.label)

    def update_frame(self):
        self.frame = self.context.get_frame(self.id)

        if self.frame is not None:
            self.image = QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], QImage.Format_Indexed8)
            self.label.setPixmap(QPixmap.fromImage(self.image))
