#!/usr/bin/python
############################################################
### Project: coin
### File: __init__.py
### Description: main file of coin
### Version: 1.0
############################################################
import sys, os, glob
import PyQt6
import gui
import tess

def main():
    model_names = tess.get_tess_model_names()

    if len(model_names) == 0:
        print("[ERR] No tesseract model found at", MODELS_PATH, file=sys.stderr)
        sys.exit(1)

    print("Available models:\n", model_names)
    
    app = PyQt6.QtWidgets.QApplication(sys.argv)
    main_window = gui.coin_gui(model_names)
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
