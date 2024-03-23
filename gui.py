############################################################
### Project: coin
### File: gui.py
### Description: handles the GUI of coin
### Version: 1.0
############################################################
import cv2, os, sys
from PIL import Image
import PyQt6
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6 import uic
from PyQt6 import QtCore, QtGui, QtWidgets
import glob
from upc import *
from constants import *
import tess

class UPCWorker(QObject):
    finished = pyqtSignal()
    update_name = pyqtSignal(list)

    # requires: upc_list is a list of list of two elements with the
    #  first element being the UPC's row number and the second being a
    #  string, containing the UPC
    def __init__(self, upc_lst):
        super().__init__()
        self.upc_lst = upc_lst

    # get_items_name(): get the names of all items using
    #  get_name_from_upc from the list of upc_list. Emits a pair of
    #  values stored in a list, the first element is the row number
    #  and the second is the item's name
    def get_items_name(self):
        for upc in self.upc_lst:
            name = get_name_from_upc(upc[1])
            self.update_name.emit([upc[0], name])
        self.finished.emit()

class coin_gui(QtWidgets.QMainWindow):
    # requires: model_names must be valid and not empty
    def __init__(self, model_names):
        print("Initializing GUI...")

        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi('coin.ui', self)

        self.ui.openButton.clicked.connect(self.open_image)
        self.ui.getNameButton.clicked.connect(self.get_all)
        self.ui.saveFileButton.clicked.connect(self.save_file)
        self.ui.saveDbButton.clicked.connect(self.save_database)

        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.ui.photo.setMouseTracking(True)
        self.ui.photo.installEventFilter(self)
        self.ui.photo.setAlignment(PyQt6.QtCore.Qt.AlignmentFlag.AlignTop)
        self.image = None
        self.scale = 1.0

        self.items = None

        if len(model_names) == 0:
            print("[ERR] No tesseract model given to coin_gui!", file=sys.stderr)
            sys.exit(1)
        self.model_names = model_names
        self.update_model(self.model_names[0])
        self.models.addItems(self.model_names)
        self.models.currentTextChanged.connect(self.update_model)
        self.models.setCurrentIndex(self.model_names.index(self.model))

        self.upc_chk_timer = QTimer(self)
        self.upc_chk_timer.timeout.connect(self.push_upc_to_thread)
        self.upc_chk_timer.start(1500)
        print("Initialized timer!")

        self.upc_thread = None
        self.upc_worker = None
        self.upc_chk_lst = []

    # open_image(): prompts to open an image, if an error occurrs, the
    #  image within the photo view will not be updated, otherwise, the
    #  image will be updated and stored in self.pixmap
    def open_image(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File')
        if filename[0] == "":
            print("No file was selected or opened!")
            return None

        print("Opening file: ", filename[0])
        self.image = cv2.imread(str(filename[0]))

        if self.image is None:
            print("Error: image is empty!", file=sys.stderr)
            print("No file was opened!")
            return None

        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0],
                       frame.strides[0], QImage.Format.Format_RGB888)

        self.pixmap = QPixmap.fromImage(image)
        self.scale = SCALE_DEFAULT
        self.update_scale()

        if self.items is not None:
            self.items.deleteLater()
        
        self.items = QStandardItemModel()
        self.itemsTable.setModel(self.items)
        self.items.setColumnCount(TABLE_COL_CNT)

        self.set_table_header()
        print("Initialized new table!")

        self.statusBar().showMessage("Opened file: " + filename[0])
        
        return None

    # save_file(): prompt to save a file, will write to the file in
    #  .csv format
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

    # save_database(): saves to a database
    def save_database(self):
        print("Not implemented!")

    # set_table_header(): sets the headers of the table when a new
    #  image is opened
    def set_table_header(self):
        for i in range(TABLE_COL_CNT):
            item = QStandardItem(TABLE_HEADERS[i])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setEditable(False)
            self.items.setItem(0, i, item)

        self.itemsTable.resizeColumnsToContents()

    # update_scale(): update the image with the new scale
    def update_scale(self):
        self.ui.photo.setPixmap(self.pixmap.scaled(
            int(self.scale * self.pixmap.width()),
            int(self.scale * self.pixmap.height())))

        print("Photo scale set to:", self.scale)
        self.statusBar().showMessage("Photo scale set to: " + str(self.scale))

    # push_upc_to_thread(): runs a new thread when there are items in
    #  self.upc_chk_lst and self.upc_thread is available
    def push_upc_to_thread(self):
        if len(self.upc_chk_lst) > 0 and self.upc_worker is None:
            self.upc_thread = QThread()
            
            self.upc_worker = UPCWorker(self.upc_chk_lst)
            self.upc_worker.moveToThread(self.upc_thread)

            self.upc_worker.update_name.connect(self.update_item_name)
            self.upc_worker.finished.connect(self.upc_thread.quit)
            self.upc_worker.finished.connect(self.delete_upc_worker)
            self.upc_thread.finished.connect(self.delete_upc_thread)

            self.upc_thread.started.connect(self.upc_worker.get_items_name)
            self.upc_thread.start()

            print("Lookup thread started!")
            
            self.upc_chk_lst = []

    # delete_upc_worker(): wrapper for self.upc_worker.deleteLater()
    def delete_upc_worker(self):
        self.upc_worker.deleteLater()
        self.upc_worker = None

    # delete_upc_thread(): wrapper for self.upc_thread.deleteLater()
    def delete_upc_thread(self):
        print("Lookup thread is finished!")
        self.upc_thread.deleteLater()

    # update_item_name(name): name is a two-element list with the
    #  first element being the row in which is item is located, and
    #  the second being a string containing the item's name
    def update_item_name(self, name):
        item = QStandardItem(name[1])
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items.setItem(name[0], TABLE_COL_NAME, item)
        self.itemsTable.resizeColumnToContents(TABLE_COL_NAME)
        self.itemsTable.resizeRowToContents(name[0])

    # get_all(): get the names of items in every row that doesn't have
    #  a name in it
    def get_all(self):
        for i in range(1, self.items.rowCount()):            
            if (self.items.item(i, TABLE_COL_NAME) is None or
                self.items.item(i, TABLE_COL_NAME).text() == "N/A"):
                upc = self.items.item(i, TABLE_COL_UPC).text()
                print("Started getting name of UPC:", upc)
                self.statusBar().showMessage("Started getting name of UPC: " + upc)
                self.upc_chk_lst.append([i, upc])
        self.push_upc_to_thread()

    # get_item_at_row(): get the name of the item at the row where the
    #  "Get" button was clicked
    def get_item_at_row(self):
        button = self.sender()
        row = self.itemsTable.indexAt(button.pos()).row()
        upc = self.items.item(row, TABLE_COL_UPC).text()
        self.upc_chk_lst.append([row, upc])
        print("Started getting name of UPC:", upc)
        self.statusBar().showMessage("Started getting name of UPC: " + upc)
        self.push_upc_to_thread()

    # del_row(): delete the row where the "Del" button was clicked
    def del_row(self):
        button = self.sender()
        index = self.itemsTable.indexAt(button.pos())
        self.items.removeRow(index.row())
        print("Removed row", index.row())
        self.statusBar().showMessage("Removed row " + str(index.row()))

    # populate_buttons(): put buttons on the table when creating a new row
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
        get_button.clicked.connect(self.get_item_at_row)

    # update_model(): update self.model to the one selected
    def update_model(self, value):
        self.model = value
        print("Model selected as:", self.model)

    # add_upc(text): adds a new row containing text in the UPC column
    def add_upc(self, text: str):
        if text == "":
            print("No text was recognized, will not add a new item!")
            return None

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

    # eventFilter(source, event): handles a few things differently
    def eventFilter(self, source, event):
        if (event.type() == QEvent.Type.MouseButtonPress and
            source is self.ui.photo):
            self.rubber_band_show(event)
            return True

        elif (event.type() == QEvent.Type.MouseMove and
              source is self.ui.photo and self.rubber_band.isVisible()):
            self.rubber_band_redraw(event)
            return True

        elif (event.type() == QEvent.Type.MouseButtonRelease and
              source is self.ui.photo and self.rubber_band.isVisible()):
            return self.rubber_band_select(event)

        elif (event.type() == QEvent.Type.Wheel and
              self.image is not None and source is self.ui.photo and
              QApplication.keyboardModifiers() ==
              Qt.KeyboardModifier.ControlModifier):
            self.image_resize(event)
            return True

        elif (event.type() == QEvent.Type.MouseButtonDblClick and
              source is self.ui.photo):
            self.open_image()
            return True

        return False

    # rubber_band_show(event): shows the rubber band for selection
    def rubber_band_show(self, event):
        self.org = self.mapFromGlobal(event.globalPosition())
        self.top_left = event.position()
        self.rubber_band.setGeometry(QRect(self.org.toPoint(), QSize()))
        self.rubber_band.show()

    # rubber_band_redraw(event): resizes the rubber band for selection
    def rubber_band_redraw(self, event):
        pos = self.mapFromGlobal(event.globalPosition()).toPoint()
        pos = QPoint(int(max(pos.x(), 0)),
                     int(max(pos.y(), 0)))
        self.rubber_band.setGeometry(
            QRect(self.org.toPoint(),
                  pos).normalized())

    # rubber_band_select(event): processes the rubber band for selection
    def rubber_band_select(self, event):
        pos = event.position()
        self.top_left = QPoint(int(max(min(pos.x(), self.top_left.x()), 0)),
                               int(max(min(pos.y(), self.top_left.y()), 0)))

        self.rubber_band.hide()
        rect = self.rubber_band.geometry()
        self.x1 = int(self.top_left.x() / self.scale)
        self.y1 = int(self.top_left.y() / self.scale)
        width = rect.width() / self.scale
        height = rect.height() / self.scale
        self.x2 = int(self.x1 + width)
        self.y2 = int(self.y1 + height)

        if (width >= WIDTH_MIN and height >= HEIGHT_MIN and
            self.image is not None):
            print("Cropped image:", self.x1, self.y1, self.x2, self.y2)
            crop = self.image[self.y1:self.y2, self.x1:self.x2]

            text = tess.image_to_text(self.model, crop)
            print("Text selected:", text)
            self.statusBar().showMessage("Text selected: " + text)
            self.add_upc(text)
            return True

        return False

    # image_resize(event): resize the image when scrolling with Ctrl
    def image_resize(self, event):
        self.scale = self.scale + event.angleDelta().y() / SCALE_DELTA

        if self.scale < SCALE_MIN:
            self.scale = SCALE_MIN
        
        if self.scale > SCALE_MAX:
            self.scale = SCALE_MAX
            
        self.update_scale()
