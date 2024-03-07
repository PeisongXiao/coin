# This module handles the GUI of coin
import pytesseract
import cv2, os, sys
from PIL import Image
import PyQt5
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5 import QtCore, QtGui, QtWidgets
import glob

# [!!!] Change this if tesseract can't find any data
models_path = '/usr/share/tessdata/'

# Automatically finds all available language models
models_list = glob.glob(models_path + "*.traineddata")
model_names = []
for path in models_list:
    base_name = os.path.basename(path)
    base_name = os.path.splitext(base_name)[0]
    model_names.append(base_name)


class coin_app(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi('selector.ui', self)
        self.image = None
        self.ui.openButton.clicked.connect(self.open)

    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File')
        print("Opening file: ", filename[0])
        self.image = cv2.imread(str(filename[0]))

        if self.image.size == 0:
            print("Error: image is empty!")

        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0],
                       frame.strides[0], QImage.Format_RGB888)

        self.ui.photo.setPixmap(QPixmap.fromImage(image))
        print("Updated photo")

app = QtWidgets.QApplication(sys.argv)
mainWindow = coin_app()
mainWindow.show()
sys.exit(app.exec_())
