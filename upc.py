import time
from seleniumbase import Driver

driver = Driver(uc=True)
driver.implicitly_wait(5)

def get_name_from_upc(upc: str, wait_interval=3, max_tries=10) -> str:
    url = "https://stocktrack.ca/wm/index.php?s=wm&upc=" + upc
    driver.get(url)

    upc = upc.lstrip("0")

    print("Removed leading 0's:", upc)

    # Change the cookies here to match that of yours when you lookup
    #  any item on stocktrack.ca to bypass the Cloudflare checks
    driver.add_cookie({
        "name": "PHPSESSID",
        "value": "9n1ic479r1bteiv758gm9hk65p",
        "path": "/",
        "domain": "stocktrack.ca"
    })
    driver.add_cookie({
        "name": "cf_chl_3",
        "value": "1d706187484b25c",
        "path": "/",
        "domain": "stocktrack.ca"
    })
    driver.add_cookie({
        "name": "cf_clearance",
        "value": "Wp8tAMUKLdS3a4Y9AT09BIlZKx4x120uC1QzBQTUluQ-1710517775-1.0.1.1-hMEP8oeggZHBkylkwkQfi2p57H6zUUvGG40d_M4vGqOqg2Zh7wZsg6KrGl3XkDUn3mXAqyZrTqlQfd5pgHCZWQ",
        "path": "/",
        "domain": "stocktrack.ca"
    })
    driver.add_cookie({
        "name": "fp",
        "value": "26f4acb9b23415f921bba6977b68d55f",
        "path": "/",
        "domain": "stocktrack.ca"
    })

    driver.refresh()
    name = ""
    str_s = "target=\"_blank\">"
    str_t = "<br>UPC: " + upc + "<br>"
    str_tt = "</a><br>SKU:"
    times = 0
    while times < max_tries:
        if __debug__:
            print("Iteration No. ", times)

        times = times + 1

        time.sleep(wait_interval)
        page = str(driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"))
        t = page.find(str_t)
        s = page.rfind(str_s, 0, t)
        tt = page.rfind(str_tt, 0, t)

        if __debug__:
            p = open("page.html", "w")
            print(page, file=p)

        if t == -1 or s == -1:
            continue
        else:
            name = page[s + len(str_s) : tt]
            break
    return name.replace("&nbsp;", "\n")
