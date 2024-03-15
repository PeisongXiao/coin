# This module handles the GUI of coin
import pytesseract
import cv2, os, sys
from PIL import Image
import PyQt6
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6 import QtCore, QtGui, QtWidgets
import glob

# [!!!] Change this if tesseract or coin can't find any data
MODELS_PATH = '/usr/share/tessdata/'

# [!!!] Sane values for scaling
SCALE_MIN = 0.3
SCALE_MAX = 4.0
# How much (in decimal) to change the scale for every degree
SCALE_DELTA = 8 * 360 * 1

# [!!!] Sane values for recognition
WIDTH_MIN = 10
HEIGHT_MIN = 10

# Automatically finds all available language models
models_list = glob.glob(MODELS_PATH + "*.traineddata")
model_names = []
for path in models_list:
    base_name = os.path.basename(path)
    base_name = os.path.splitext(base_name)[0]
    model_names.append(base_name)
if len(model_names) == 0:
    print("No tesseract models found at", MODELS_PATH, "!", file=sys.stderr)
    sys.exit(0)


class coin_app(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi('coin.ui', self)
        self.image = None

        self.ui.openButton.clicked.connect(self.open)
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.ui.photo.setMouseTracking(True)
        self.ui.photo.installEventFilter(self)
        self.ui.photo.setAlignment(PyQt6.QtCore.Qt.AlignmentFlag.AlignTop)

        self.model = model_names[0]
        print("Model selected as:", self.model)
        self.models.addItems(model_names)
        self.models.currentTextChanged.connect(self.update_now)
        self.models.setCurrentIndex(model_names.index(self.model))

        self.items = QStandardItemModel()
        self.itemsTable.setModel(self.items)
        self.items.setColumnCount(1)

        self.scale = 1.0

    def update_now(self, value):
        self.model = value
        print("Model selected as:", self.model)
        
    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File')
        print("Opening file: ", filename[0])
        self.image = cv2.imread(str(filename[0]))

        if self.image.size == 0:
            print("Error: image is empty!", file=sys.stderr)

        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0],
                       frame.strides[0], QImage.Format.Format_RGB888)

        self.pixmap = QPixmap.fromImage(image)
        self.ui.photo.setPixmap(self.pixmap)
        self.scale = 1.0
        print("Updated photo!")
        print("Photo scale set to:", self.scale)

    def scale_update(self):
        self.ui.photo.setPixmap(self.pixmap.scaled(
            int(self.scale * self.pixmap.width()),
            int(self.scale * self.pixmap.height())))
        print("Photo scale set to:", self.scale)

    def image_to_text(self, cropped_image):
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 1)
        crop = Image.fromarray(gray)
        text = pytesseract.image_to_string(crop, lang=self.model)
        print("Text selected:", text)
        return text

    def eventFilter(self, source, event):
        # Handling the selection box
        if event.type() == QEvent.Type.MouseButtonPress and source is self.ui.photo:
            self.org = self.mapFromGlobal(event.globalPosition())
            self.top_left = event.position()
            self.rubberBand.setGeometry(QRect(self.org.toPoint(), QSize()))
            self.rubberBand.show()
            return True

        elif event.type() == QEvent.Type.MouseMove and source is self.ui.photo:
            if self.rubberBand.isVisible():
                pos = self.mapFromGlobal(event.globalPosition()).toPoint()
                pos = QPoint(int(max(pos.x(), 0)),
                             int(max(pos.y(), 0)))
                self.rubberBand.setGeometry(
                    QRect(self.org.toPoint(),
                          pos).normalized())
                return True

        elif event.type() == QEvent.Type.MouseButtonRelease and source is self.ui.photo:
            pos = event.position()
            self.top_left = QPoint(int(max(min(pos.x(), self.top_left.x()), 0)),
                                   int(max(min(pos.y(), self.top_left.y()), 0)))
            if self.rubberBand.isVisible():
                self.rubberBand.hide()
                rect = self.rubberBand.geometry()
                self.x1 = int(self.top_left.x() / self.scale)
                self.y1 = int(self.top_left.y() / self.scale)
                width = rect.width() / self.scale
                height = rect.height() / self.scale
                self.x2 = int(self.x1 + width)
                self.y2 = int(self.y1 + height)
            else:
                return False
            if width >= WIDTH_MIN and height >= HEIGHT_MIN and self.image is not None:
                print("Cropped image:", self.x1, self.y1, self.x2, self.y2)
                self.crop = self.image[self.y1:self.y2, self.x1:self.x2]
                cv2.imwrite("cropped.png", self.crop)
                self.text = self.image_to_text(self.crop)
                ##self.ui.textEdit()
                return True

        # Resizing the photo
        elif event.type() == QEvent.Type.Wheel and self.image is not None and source is self.ui.photo:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                self.scale = self.scale + event.angleDelta().y() / SCALE_DELTA
                if self.scale < SCALE_MIN:
                    self.scale = SCALE_MIN
                if self.scale > SCALE_MAX:
                    self.scale = SCALE_MAX
                self.scale_update()
                return True
        elif event.type() == QEvent.Type.MouseButtonDblClick and source is self.ui.photo:
            self.open()
            return True
        return False

app = QtWidgets.QApplication(sys.argv)
mainWindow = coin_app()
mainWindow.show()
sys.exit(app.exec())
