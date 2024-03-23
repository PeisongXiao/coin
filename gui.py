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
import upc
from upc import get_name_from_upc

# [!!!] Change this if tesseract or coin can't find any data
MODELS_PATH = '/usr/share/tessdata/'

# [!!!] Sane values for scaling
SCALE_MIN   = 0.3
SCALE_MAX   = 4.0
# How much (in decimal) to change the scale for every degree
SCALE_DELTA = 8 * 360 * 1

# [!!!] Sane values for recognition
WIDTH_MIN  = 10
HEIGHT_MIN = 10

# Column Information
TABLE_COL_CNT   = 5
TABLE_COL_GET   = 0
TABLE_COL_DEL   = 1
TABLE_COL_UPC   = 2
TABLE_COL_NAME  = 3
TABLE_COL_PRICE = 4

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

class UPCWorker(QObject):
    finished = pyqtSignal()
    update_name = pyqtSignal(list)
    
    def __init__(self, upcList):
        super().__init__()
        self.upcList = upcList

    def get_items_name(self):
        for upc in self.upcList:
            name = get_name_from_upc(upc[1])
            self.update_name.emit([upc[0], name])
        self.finished.emit()

class coin_app(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi('coin.ui', self)
        self.image = None

        self.ui.openButton.clicked.connect(self.open)
        self.ui.getNameButton.clicked.connect(self.get_all)
        self.ui.saveFileButton.clicked.connect(self.save_file)
        self.ui.saveDbButton.clicked.connect(self.save_database)

        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.ui.photo.setMouseTracking(True)
        self.ui.photo.installEventFilter(self)
        self.ui.photo.setAlignment(PyQt6.QtCore.Qt.AlignmentFlag.AlignTop)

        self.model = model_names[0]
        print("Model selected as:", self.model)
        self.models.addItems(model_names)
        self.models.currentTextChanged.connect(self.update_now)
        self.models.setCurrentIndex(model_names.index(self.model))

        self.scale = 1.0

        self.items = None

        self.upcCheckTimer = QTimer(self)
        self.upcCheckTimer.timeout.connect(self.pushUPCToThread)
        self.upcCheckTimer.start(1500)
        print("Initialized timer!")

        self.upcThread = QThread()
        self.upcWorker = None
        self.upcCheckList = []

    def pushUPCToThread(self):
        if len(self.upcCheckList) > 0 and self.upcWorker is None:
            self.upcWorker = UPCWorker(self.upcCheckList)
            self.upcWorker.moveToThread(self.upcThread)

            self.upcWorker.update_name.connect(self.updateItemName)
            self.upcWorker.finished.connect(self.collectUPCWorker)
            self.upcThread.finished.connect(self.collectUPCThread)

            self.upcThread.started.connect(self.upcWorker.get_items_name)
            self.upcThread.start()

            print("Lookup thread started!")
            
            self.upcCheckList = []

    def collectUPCWorker(self):
        self.upcWorker.deleteLater()
        self.upcWorker = None

    def collectUPCThread(self):
        self.upcThread.deleteLater()

    def updateItemName(self, name):
        itemName = QStandardItem(name[1])
        itemName.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items.setItem(name[0], TABLE_COL_NAME, itemName)
        self.itemsTable.resizeColumnToContents(TABLE_COL_NAME)
        self.itemsTable.resizeRowToContents(name[0])

    def update_now(self, value):
        self.model = value
        print("Model selected as:", self.model)

    def set_table_header(self):
        item = QStandardItem(" Get ")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setEditable(False)
        self.items.setItem(0, TABLE_COL_GET, item)
        item = QStandardItem(" Del ")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setEditable(False)
        self.items.setItem(0, TABLE_COL_DEL, item)
        item = QStandardItem("UPC")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setEditable(False)
        self.items.setItem(0, TABLE_COL_UPC, item)
        item = QStandardItem("Item Name")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setEditable(False)
        self.items.setItem(0, TABLE_COL_NAME, item)
        item = QStandardItem("Price")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setEditable(False)
        self.items.setItem(0, TABLE_COL_PRICE, item)
        self.itemsTable.resizeColumnsToContents()
        
    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File')
        if filename[0] == "":
            print("No file was selected or opened!")
            return None

        if self.items is not None:
            self.items.deleteLater()

        print("Opening file: ", filename[0])
        self.image = cv2.imread(str(filename[0]))

        if self.image is None:
            print("Error: image is empty!", file=sys.stderr)
            return None

        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0],
                       frame.strides[0], QImage.Format.Format_RGB888)

        self.pixmap = QPixmap.fromImage(image)
        self.ui.photo.setPixmap(self.pixmap)
        self.scale = 1.0
        print("Updated photo!")
        print("Photo scale set to:", self.scale)

        self.items = QStandardItemModel()
        self.itemsTable.setModel(self.items)
        self.items.setColumnCount(TABLE_COL_CNT)

        self.set_table_header()
        print("Initialized new table!")

        self.statusBar().showMessage("Opened file: " + filename[0])
        
        return None

    def save_file(self):
        filename = QFileDialog.getSaveFileName(self, 'Select File')

        if filename[0] == "":
            print("No file was selected or opened!")
            return None

        out = open(filename[0], "w")

        for i in range(self.items.rowCount()):
            print(self.items.item(i,TABLE_COL_UPC).text(), file=out, end=", ")
            name = self.items.item(i,TABLE_COL_NAME).text()
            name = name.replace("\n", " ").replace('"', '""')
            print(name, file=out, end=", ")
            print(self.items.item(i,TABLE_COL_PRICE).text().replace("\n", " "),
                  file=out)
        out.close()

        self.statusBar().showMessage("Saved to: " + filename[0])

    def save_database(self):
        print("Not implemented!")

    def scale_update(self):
        self.ui.photo.setPixmap(self.pixmap.scaled(
            int(self.scale * self.pixmap.width()),
            int(self.scale * self.pixmap.height())))
        print("Photo scale set to:", self.scale)

        self.statusBar().showMessage("Photo scale set to: " + str(self.scale))

    def image_to_text(self, cropped_image):
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 1)
        crop = Image.fromarray(gray)
        text = pytesseract.image_to_string(crop, lang=self.model).strip()
        print("Text selected:", text)
        return text

    def get_row(self):
        button = self.sender()
        row = self.itemsTable.indexAt(button.pos()).row()
        upc = self.items.item(row, TABLE_COL_UPC).text()
        self.upcCheckList.append([row, upc])
        print("Started getting name of UPC:", upc)
        self.statusBar().showMessage("Started getting name of UPC: " + upc)
        self.pushUPCToThread()

    def get_all(self):
        for i in range(1, self.items.rowCount()):            
            if self.items.item(i, TABLE_COL_NAME) is None or self.items.item(i, TABLE_COL_NAME).text() == "N/A":
                upc = self.items.item(i, TABLE_COL_UPC).text()
                print("Started getting name of UPC:", upc)
                self.statusBar().showMessage("Started getting name of UPC: " + upc)
                self.upcCheckList.append([i, upc])
        self.pushUPCToThread()

    def del_row(self):
        button = self.sender()
        index = self.itemsTable.indexAt(button.pos())
        self.items.removeRow(index.row())
        print("Removed row", index.row())

    def populate_buttons(self):
        del_button = QPushButton("Del")
        self.itemsTable.setIndexWidget(
            self.items.index(self.items.rowCount() - 1, TABLE_COL_DEL),
            del_button)
        del_button.clicked.connect(self.del_row)

        get_button = QPushButton("Get")
        self.itemsTable.setIndexWidget(
            self.items.index(self.items.rowCount() - 1, TABLE_COL_GET),
            get_button)
        get_button.clicked.connect(self.get_row)

    def add_upc(self, text: str):
        if text == "":
            print("No text was recognized, will not add a new item!")
            return None
        self.statusBar().showMessage("Text selected: " + text)
        item = QStandardItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items.setItem(self.items.rowCount(), TABLE_COL_UPC, item)

        item = QStandardItem("N/A")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items.setItem(self.items.rowCount() - 1, TABLE_COL_NAME, item)
        item = QStandardItem("N/A")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items.setItem(self.items.rowCount() - 1, TABLE_COL_PRICE, item)

        self.populate_buttons()
        self.itemsTable.resizeColumnToContents(TABLE_COL_UPC)
        return None

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
                # cv2.imwrite("cropped.png", self.crop)
                self.text = self.image_to_text(self.crop)
                self.add_upc(self.text)
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
