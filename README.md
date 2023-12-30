# Immowelt Webscraper
Scrapes the german [Immowelt](https://www.immowelt.de/) website for real estate.

## Installation
Navigate to the requirements.txt file and run:
```sh
  pip install -r requirements.txt
  ```
## Usage
Run ImmoweltScraper.py with the following arguments:
```sh
options:
  -h, --help            show this help message and exit

required arguments:
  -c CITY, --city CITY  City to scrape
  -p {kaufen,mieten}, --payment_type {kaufen,mieten}
                        Payment type

optional arguments:
  -n NUM_PAGES, --num_pages NUM_PAGES
                        Number of pages to scrape
  ```
Since websites change constantly, this script might not work in the future.
