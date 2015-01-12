from PySide.QtCore import *
from PySide.QtGui import *

import sys


class Main(QWidget):

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        layout  = QVBoxLayout(self)

        picture = PictureLabel("mini-test.jpg", self)
        picture.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout.addWidget(picture)
        layout.addWidget(QLabel("Click for foreground. Shift + Click for background."))

class PictureLabel(QLabel):
    BACKGROUND_POINTS_COLOR = QColor(180, 50, 50, 100)
    FOREGROUND_POINTS_COLOR = QColor(50, 180, 50, 100)
    WANTED_WIDTH = 500.

    def __init__(self, image_path, parent=None):
        super(PictureLabel, self).__init__(parent)
        self.image_raw = QImage(image_path)
        self.image = QPixmap(self.image_raw)

        # Scaling
        self.scale = max(1, int(self.WANTED_WIDTH / self.image_raw.width()))
        self.image = self.image.scaled(self.image.size() * self.scale)
        self.setPixmap(QPixmap(self.image))

        self.background_points = set()
        self.foreground_points = set()

    def print_pixels(self):
        w, h = self.image_raw.width(), self.image_raw.height()
        for i in xrange(w):
            for j in xrange(h):
                print qRed(self.image_raw.pixel(i, j)),
            print

    def mousePressEvent(self, event):
        self.new_point(event)

    def mouseMoveEvent(self, event):
        self.new_point(event)

    def new_point(self, event):
        # Getting the point's coordinates
        point = (event.x() / self.scale, event.y() / self.scale)

        # Ignoring the point if it was already in either of the sets
        for points_set in [self.background_points, self.foreground_points]:
            if point in points_set:
                #points_set.remove(point)
                return

        # Adding the point to the appropriate set
        background = event.modifiers() == Qt.ShiftModifier
        chosen_set = self.background_points if background else self.foreground_points
        chosen_set.add(point)

        self.repaint()

    def paintEvent(self, event):
        super(PictureLabel, self).paintEvent(event)
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.image)

        # Drawing background points
        painter.setPen(PictureLabel.BACKGROUND_POINTS_COLOR)
        painter.setBrush(PictureLabel.BACKGROUND_POINTS_COLOR)
        for point in self.background_points:
            painter.drawRect(point[0] * self.scale, point[1] * self.scale, self.scale, self.scale)

        # Drawing foreground points
        painter.setPen(PictureLabel.FOREGROUND_POINTS_COLOR)
        painter.setBrush(PictureLabel.FOREGROUND_POINTS_COLOR)
        for point in self.foreground_points:
            painter.drawRect(point[0] * self.scale, point[1] * self.scale, self.scale, self.scale)


a = QApplication([])
m = Main()
m.show()
sys.exit(a.exec_())
