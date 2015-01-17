import sys

from PySide.QtCore import *
from PySide.QtGui import *

from image import SegmentedImage


class Main(QWidget):

    def __init__(self, image_path, parent=None):
        super(Main, self).__init__(parent)

        layout  = QVBoxLayout(self)
        picture = PictureLabel(image_path, self)
        picture.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout.addWidget(picture)

        # Setting up sliders
        self.lambda_slider = self.setup_slider("Lambda", layout, 1, 500)
        self.sigma_slider = self.setup_slider("Sigma", layout, 1, 500)


        layout.addWidget(QLabel("Click for foreground. Shift + Click for background. Ctrl + Click to remove seeds.\nR to launch the segmentation, S to toggle the segmentation view."))

    def setup_slider(self, title, layout, minVal, maxVal):
        s_layout  = QHBoxLayout()
        slider = QSlider()
        slider.setOrientation(Qt.Horizontal)
        slider.setRange(minVal, maxVal)
        slider.setTickPosition(QSlider.TicksAbove)
        label = QLabel(title)

        def callback(new_value):
            label.setText("{}: {}".format(title, new_value))
        slider.valueChanged.connect(callback)
        slider.setValue(2)

        s_layout.addWidget(label)
        s_layout.addWidget(slider)

        layout.addLayout(s_layout)
        return slider

class PictureLabel(QLabel):
    BACKGROUND_SEEDS_COLOR = QColor(180, 50, 50, 150)
    FOREGROUND_SEEDS_COLOR = QColor(50, 180, 50, 150)

    BACKGROUND_POINTS_COLOR = QColor(180, 50, 50, 80)
    FOREGROUND_POINTS_COLOR = QColor(50, 180, 50, 80)
    WANTED_WIDTH = 800.

    def __init__(self, image_path, parent=None):
        super(PictureLabel, self).__init__(parent)
        self.parent = parent
        self.segmented_image = SegmentedImage(image_path)
        self.image_raw = QImage(image_path)
        self.image = QPixmap(self.image_raw)

        # Scaling
        self.scale = max(1, int(self.WANTED_WIDTH / self.image_raw.width()))
        self.image = self.image.scaled(self.image.size() * self.scale)
        self.setPixmap(QPixmap(self.image))

        # Seeds, chosen by the user
        self.bkg_seeds = set()
        self.obj_seeds = set()

        # Points, chosen by the calculated segmentation from the given seeds
        self.bkg_points = set()
        self.obj_points = set()

        self.segmentation_shown = True

        self.setFocus()

    def mousePressEvent(self, event):
        self.new_click(event)

    def mouseMoveEvent(self, event):
        self.new_click(event)

    def keyReleaseEvent(self, event):
        super(PictureLabel, self).keyReleaseEvent(event)
        # Re-segmenting the image
        if event.key() == Qt.Key_R and (self.obj_seeds and self.bkg_seeds):
            self.obj_points, self.bkg_points = self.segmented_image.segmentation(self.obj_seeds, self.bkg_seeds, self.parent.lambda_slider.value(), self.parent.sigma_slider.value())
        if event.key() == Qt.Key_S:
            self.segmentation_shown = not self.segmentation_shown

        self.repaint()

    def new_click(self, event):
        # Getting the point's coordinates
        point = (event.x() / self.scale, event.y() / self.scale)
        if not (0 <= point[0] < self.segmented_image.w and 0 <= point[1] < self.segmented_image.h):
            return

        # Ignoring the point if it was already in either of the sets, or deleting it if CTRL is pressed
        for points_set in [self.bkg_seeds, self.obj_seeds]:
            if point in points_set:
                if event.modifiers() == Qt.ControlModifier:
                    points_set.remove(point)
                    self.repaint()
                return
        if event.modifiers() == Qt.ControlModifier:
            return

        # Automatically resetting the segmentation when adding new points
        if self.obj_points:
            self.obj_points = set()
        if self.bkg_points:
            self.bkg_points = set()

        # Adding the point to the appropriate set
        background = event.modifiers() == Qt.ShiftModifier
        chosen_set = self.bkg_seeds if background else self.obj_seeds
        chosen_set.add(point)

        self.repaint()

    def paintEvent(self, event):
        super(PictureLabel, self).paintEvent(event)
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.image)

        # Drawing background seeds
        painter.setPen(PictureLabel.BACKGROUND_SEEDS_COLOR)
        painter.setBrush(PictureLabel.BACKGROUND_SEEDS_COLOR)
        for point in self.bkg_seeds:
            painter.drawRect(point[0] * self.scale, point[1] * self.scale, self.scale, self.scale)

        # Drawing foreground seeds
        painter.setPen(PictureLabel.FOREGROUND_SEEDS_COLOR)
        painter.setBrush(PictureLabel.FOREGROUND_SEEDS_COLOR)
        for point in self.obj_seeds:
            painter.drawRect(point[0] * self.scale, point[1] * self.scale, self.scale, self.scale)

        if not self.segmentation_shown:
            return

        # Drawing background points
        painter.setPen(PictureLabel.BACKGROUND_POINTS_COLOR)
        painter.setBrush(PictureLabel.BACKGROUND_POINTS_COLOR)
        for point in self.bkg_points:
            painter.drawRect(point[0] * self.scale, point[1] * self.scale, self.scale, self.scale)

        # Drawing foreground points
        painter.setPen(PictureLabel.FOREGROUND_POINTS_COLOR)
        painter.setBrush(PictureLabel.FOREGROUND_POINTS_COLOR)
        for point in self.obj_points:
            painter.drawRect(point[0] * self.scale, point[1] * self.scale, self.scale, self.scale)



if __name__ == '__main__':
    a = QApplication([])
    image_path = sys.argv[1] if len(sys.argv) > 1 else 'mini-test.jpg'
    m = Main(image_path)
    m.show()
    sys.exit(a.exec_())
