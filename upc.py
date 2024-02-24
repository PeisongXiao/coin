import time
from seleniumbase import Driver

driver = Driver(uc=True)
driver.implicitly_wait(5)

def get_name_from_upc(upc: str) -> str:
    url = "https://stocktrack.ca/wm/index.php?s=wm&upc=" + upc
    driver.get(url)
    driver.add_cookie({
        "name": "PHPSESSID",
        "value": "835ttgvbgncf4uq82dpagmk688",
        "path": "/",
        "domain": "stocktrack.ca"
    })
    driver.add_cookie({
        "name": "cf_chl_3",
        "value": "1fad2e046cb9148",
        "path": "/",
        "domain": "stocktrack.ca"
    })
    driver.add_cookie({
        "name": "cf_clearance",
        "value": "LUZoWRwn3n1wBEv7bY1XinLQbX0ZTAnggLIfkoy2S60-1708745781-1.0-AXqZtJSIQrq/6/H03NLlHwbpLA1tJmPjgjMJhzaczZjGabhR6ow16wMK5pTwilZiqK7C7fdcYvM0qsbAARkLGEU=",
        "path": "/",
        "domain": "stocktrack.ca"
    })
    driver.refresh()
    name = ""
    str_s = "target=\"_blank\">"
    str_t = "</a><br>UPC: " + upc + "<br>"
    times = 0
    while True:
        if __debug__:
            print("Iteration No. ", times)
            times = times + 1

        time.sleep(20)
        page = str(driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"))
        t = page.find(str_t)
        s = page.rfind(str_s, 0, t)

        if __debug__:
            print(page[s + len(str_s) : t - 1])

        if t == -1 or s == -1:
            continue
        else:
            name = page[s + len(str_s) : t - 1]
            break
    return name
