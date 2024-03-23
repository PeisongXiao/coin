############################################################
### Project: coin
### File: upc.py
### Description: scapes the item's name by using the its UPC
### Version: 1.0
############################################################
import time
from seleniumbase import Driver
from constants import *

driver = Driver(uc=True)
driver.implicitly_wait(5)

# get_name_from_upc(upc, wait_interval, max_tries): will try to get
#  the item's name from stocktrack.ca.
def get_name_from_upc(upc: str, wait_interval=1, max_tries=30) -> str:
    url = "https://stocktrack.ca/wm/index.php?s=wm&upc=" + upc
    driver.get(url)

    upc = upc.lstrip("0")

    print("Removed leading 0's:", upc)

    for cookie in COOKIE_DICT_LIST:
        driver.add_cookie(cookie)

    driver.refresh()
    name = ""
    pattern_front = "target=\"_blank\">"
    pattern_back_upc = "<br>UPC: " + upc + "<br>"
    pattern_back_sku = "</a><br>SKU:"

    tries = 0

    while tries < max_tries:
        if __debug__:
            print("Iteration No.", tries)

        tries = tries + 1

        time.sleep(wait_interval)
        page = str(driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"))

        back_upc_idx = page.find(pattern_back_upc)
        front_idx = page.rfind(pattern_front, 0, back_upc_idx)
        back_sku_idx = page.rfind(pattern_back_sku, 0, back_upc_idx)

        if __debug__:
            p = open("page.html", "w")
            print(page, file=p)

        if back_upc_idx == -1 or front_idx == -1:
            continue
        else:
            name = page[front_idx + len(pattern_front) : back_sku_idx]
            break

    return name.replace("&nbsp;", "\n")
