import argparse
import math
from time import sleep
from urllib.request import urlopen

import pandas as pd
from bs4 import BeautifulSoup


class ImmoweltScraper:
    def __init__(self, city, payment_type, num_pages=math.inf):
        self.payment_type = payment_type
        self.city = city
        self.url = f"https://www.immowelt.de/suche/{self.city}/wohnungen/{self.payment_type}?d=true&sd=DESC&sf=TIMESTAMP"
        self.data_dict = {
            "Name": [],
            "Link": [],
            "Preis": [],
            "Fläche(m²)": [],
            "Zimmer": [],
            "Straße": [],
            "Ort": [],
            "Baujahr": [],
            "Bezug": [],
            "Geschoss": [],
            "Energieausweis": [],
            "Heizungsart": [],
            "Energieträger": [],
            "Haustyp": [],
            "Aufzug": [],
            "Küche": [],
            "Böden": [],
            "Klima/Belüftung": [],
            "Stellplatz": [],
            "möbliert": [],
            "Wellness": [],
            "TV": [],
            "Balkon/Terrasse": [],
            "Serviceleistungen": [],
            "Sicherheitstechnik": [],
            "Ausblick": [],
            "Wohnungslage": [],
            "derzeitige Nutzung": [],
            "Zustand": [],
            "Fenster": [],
            "Kommunikation": [],
            "Sonstiges/Wohnen": [],
            "Sanitär": [],
            "Versorgung": [],
            "Gebäudetyp": [],
            "Endenergiebedarf": [],
            "Wesentliche Energieträger": [],
            "Gültigkeit": [],
            "Effizienzklasse": [],
            "Energieausweistyp": [],
            "Baujahr laut Energieausweis": [],
            "Endenergieverbrauch": [],
            "Derzeitige Nutzung": [],
            "Kategorie": [],
            "Endenergiebedarf (Wärme)": [],
            "Endenergieverbrauch (Wärme)": [],
            "Endenergieverbrauch (Strom)": [],
            "Endenergiebedarf (Strom)": [],
            "Geschosse": [],
            "Warmmiete": [],
            "Heizkosten": [],
            "Nebenkosten": [],
            "Hausgeld": [],
            "1 Stellplatz": [],
        }
        self.keys = []
        self.values = []

        try:
            html = urlopen(self.url).read().decode("utf-8")
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            raise Exception(f"Error getting page {self.url}: {e}")
        try:
            number_of_exposes = int(
                soup.find_all("h1", class_="MatchNumber-a225f")[0]
                .text.split(" ")[0]
                .replace(".", "")
            )
            self.num_pages = min(math.ceil(number_of_exposes / 20), num_pages)
        except Exception as e:
            print(f"Error getting number of pages: {e}")
            self.num_pages = 1

    def get_page(self, page_number):
        try:
            html = urlopen(self.url + "&sp=" + str(page_number)).read().decode("utf-8")
            soup = BeautifulSoup(html, "lxml")
            return soup
        except Exception as e:
            print(f"Error getting page {page_number}:\n{e}")

    def has_numbers(self, string):
        return any(c.isdigit() for c in string)

    def process_metadata(self, metadata):
        if metadata is None:
            return
        # process name
        self.keys.append("Name")
        self.values.append(metadata.find("h1", class_="ng-star-inserted").text)
        # process price
        price = metadata.find("strong").text.split()[0]
        price = price.replace(".", "").replace(",", ".")

        if self.has_numbers(price):
            self.keys.append("Preis")
            self.values.append(float(price))

        space, rooms, street, zip_code = metadata.find_all("span")[:4]
        # process space
        space = space.text.split()[0].replace(",", ".")
        if self.has_numbers(space):
            self.keys.append("Fläche(m²)")
            self.values.append(float(space))
        # process street
        street = street.text
        if not street == "Straße nicht freigegeben":
            self.keys.append("Straße")
            self.values.append(street)
        # process rooms
        rooms = rooms.text.replace(",", ".")
        if self.has_numbers(rooms):
            self.keys.append("Zimmer")
            self.values.append(float(rooms))
        # process zip code
        self.keys.append("Ort")
        self.values.append(zip_code.text)

    def process_estate_information(self, estate_information):
        if estate_information is not None:
            infos = estate_information.find_all("p")
            for i in range(0, len(infos) - 1, 2):
                self.keys.append(infos[i].text)
                self.values.append(infos[i + 1].text)

    def process_energy_information(self, energy_information):
        if energy_information is not None:
            infos = energy_information.find_all("p")
            for i in range(0, len(infos) - 1, 2):
                self.keys.append(infos[i].text)
                self.values.append(infos[i + 1].text)

    def process_price_information(self, price_information):
        if price_information is not None:
            infos = price_information.find_all("sd-cell-col")
            for i in range(0, len(infos) - 1, 2):
                self.keys.append(infos[i].text)
                self.values.append(infos[i + 1].text)

    def add_to_dict(self, keys, values):
        for key, value in zip(keys, values):
            if key in self.data_dict.keys():
                self.data_dict[key].append(value)

        # Add None for missing keys
        missing_keys = list(set(self.data_dict.keys()) - set(keys))
        for key in missing_keys:
            self.data_dict[key].append(None)

    def get_data(self, soup):
        expose_links = []
        for paragraph in soup.find_all("a"):
            if r"/expose/" in str(paragraph.get("href")):
                expose_links.append(paragraph.get("href").split("#")[0])
            expose_links = list(set(expose_links))
        for item in expose_links:
            self.keys, self.values = [], []
            try:
                html = urlopen(item).read().decode("utf-8")
                soup = BeautifulSoup(html, "lxml")
                self.keys.append("Link")
                self.values.append(item)
                try:
                    metadata = soup.find("app-objectmeta", id="aUebersicht")
                    self.process_metadata(metadata)
                except Exception as e:
                    print(f"Error occured with metadata: {e}")
                try:
                    estate_information = soup.find("app-estate-object-informations")
                    self.process_estate_information(estate_information)
                except Exception as e:
                    print(f"Error occured with estate information: {e}")
                try:
                    price_information = soup.find("app-price")
                    self.process_price_information(price_information)
                except Exception as e:
                    print(f"Error occured with price information: {e}")
                try:
                    energy_information = soup.find("app-energy-certificate")
                    self.process_energy_information(energy_information)
                except Exception as e:
                    print(f"Error occured with energy information: {e}")
            except Exception as e:
                print(f"Error occured with link {item}: {e}")

            self.add_to_dict(self.keys, self.values)
            sleep(1)  # sleep to limit amount of requests

    def scrape(self):
        for i in range(1, self.num_pages + 1):
            print(f"Scraping page {i} of {self.num_pages}")
            soup = self.get_page(i)
            self.get_data(soup)
            sleep(5)  # sleep to limit amount of requests

    def to_dataframe(self):
        df = pd.DataFrame(self.data_dict)
        return df.dropna(axis=1, how="all")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ImmoweltScraper.py",
        description="Scrapes Immowelt for real estate data",
        epilog="Since websites change constantly, this script might not work in the future.",
    )
    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    required.add_argument(
        "-c", "--city", type=str, help="City to scrape", default="koeln", required=True
    )
    required.add_argument(
        "-p",
        "--payment_type",
        type=str,
        help="Payment type",
        default="kaufen",
        choices=["kaufen", "mieten"],
        required=True,
    )
    optional.add_argument(
        "-n",
        "--num_pages",
        type=int,
        help="Number of pages to scrape",
        default=math.inf,
        required=False,
    )
    args = parser.parse_args()

    if args.city.isalpha():
        city = args.city.lower()
    else:
        raise ValueError("City must only contain alphabetic characters")

    if args.num_pages is not None and args.num_pages < 1:
        raise ValueError("Number of pages must be positive")

    umlaut_map = {ord("ä"): "ae", ord("ü"): "ue", ord("ö"): "oe", ord("ß"): "ss"}
    city = city.translate(umlaut_map)

    scraper = ImmoweltScraper(
        city=city, payment_type=args.payment_type, num_pages=args.num_pages
    )
    scraper.scrape()
    df = scraper.to_dataframe()
    df.to_csv(f"immowelt_{city}_{args.payment_type}.csv", index=False)
