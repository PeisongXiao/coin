############################################################
### Project: coin
### File: constants.py
### Description: defines all the constants
### Version: 1.0
############################################################
# Change this if tesseract or coin can't find any data
MODELS_PATH = '/usr/share/tessdata/'

# Sane values for scaling
SCALE_MIN     = 0.2
SCALE_MAX     = 5.0
SCALE_DEFAULT = 1.0
# How much (in decimal) to change the scale for every degree
SCALE_DELTA = 8 * 360 * 1

# Sane values for text recognition
WIDTH_MIN  = 10
HEIGHT_MIN = 10

# Table info
TABLE_COL_CNT   = 5
TABLE_COL_GET   = 0
TABLE_COL_DEL   = 1
TABLE_COL_UPC   = 2
TABLE_COL_NAME  = 3
TABLE_COL_PRICE = 4
TABLE_HEADERS = ["  Get  ", "  Del  ", "UPC", "Item Name", "Price"]

# Cookies for upc.py
COOKIE_DICT_LIST = [
    {
        "name": "PHPSESSID",
        "value": "9n1ic479r1bteiv758gm9hk65p",
        "path": "/",
        "domain": "stocktrack.ca"
    },
    {
        "name": "cf_chl_3",
        "value": "1d706187484b25c",
        "path": "/",
        "domain": "stocktrack.ca"
    },
    {
        "name": "cf_clearance",
        "value": "Wp8tAMUKLdS3a4Y9AT09BIlZKx4x120uC1QzBQTUluQ-1710517775-1.0.1.1-hMEP8oeggZHBkylkwkQfi2p57H6zUUvGG40d_M4vGqOqg2Zh7wZsg6KrGl3XkDUn3mXAqyZrTqlQfd5pgHCZWQ",
        "path": "/",
        "domain": "stocktrack.ca"
    },
    {
        "name": "fp",
        "value": "26f4acb9b23415f921bba6977b68d55f",
        "path": "/",
        "domain": "stocktrack.ca"
    }]
