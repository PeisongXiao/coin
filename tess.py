############################################################
### Project: coin
### File: tess.py
### Description: handles all pytesseract-related operations
### Version: 1.0
############################################################
import sys, os, glob
import cv2
from PIL import Image
import pytesseract
from constants import *

# get_tess_model_names(models_path): automatically finds all available
#  language models in models_path
def get_tess_model_names(models_path=MODELS_PATH):
    models_list = glob.glob(models_path + "*.traineddata")
    model_names = []
    for path in models_list:
        base_name = os.path.basename(path)
        base_name = os.path.splitext(base_name)[0]
        model_names.append(base_name)
    return model_names

# image_to_text(model, cropped_image): use the model with the name
#  model to try to recognize the text in cropped_image
def image_to_text(model, cropped_image):
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 1)
    crop = Image.fromarray(gray)
    text = pytesseract.image_to_string(crop, lang=model).strip()
    return text
