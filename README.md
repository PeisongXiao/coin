# coin
Something to coin the items on your receipts

## Why coin?
Because normal humans can't decipher what's on the Walmart receipts.


## How does coin work?
First, coins pulls the UPC and price info off of the given Walmart
receipt.

Then, coin matches the name with the UPC (Yes! No more scratching your
head against seemingly random Walmart abbreviations for items!) using
a scraper.

Finally, it stores your shopping trip in a spreadsheet (.csv format).


## Dependencies
-   Python
-   PyQt6
-   pytesseract
-   OpenCV (On Python)
-   PIL
-   Selenium (undetected, with a suitable chromedriver)

