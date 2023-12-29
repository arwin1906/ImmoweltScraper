import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from bs4 import BeautifulSoup

from ImmoweltScraper import ImmoweltScraper


class TestImmoweltScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ImmoweltScraper("koeln", "kaufen")
        self.scraper.num_pages = 2

    def test_has_numbers(self):
        self.assertTrue(self.scraper.has_numbers("abc123"))
        self.assertFalse(self.scraper.has_numbers("abc"))
        self.assertFalse(self.scraper.has_numbers(""))

    def test_get_page(self):
        soup = self.scraper.get_page(1)
        self.assertIsInstance(soup, BeautifulSoup)

    def test_process_metadata(self):
        # Mock tag object
        class MockTag:
            def __init__(self, text):
                self.text = text

        # Mock metadata object
        class MockMetadata:
            def find(self, tag, class_=None):
                if tag == "h1":
                    return MockTag("Test Name")
                elif tag == "strong":
                    return MockTag("123,45 €")
                else:
                    return [
                        MockTag("100,00 m²"),
                        MockTag("3"),
                        MockTag("Test Street"),
                        MockTag("12345 Test City"),
                    ]

            def find_all(self, tag):
                return [
                    MockTag("100,00 m²"),
                    MockTag("3"),
                    MockTag("Test Street"),
                    MockTag("12345 Test City"),
                ]

        metadata = MockMetadata()
        self.scraper.process_metadata(metadata)
        self.assertEqual(
            self.scraper.keys,
            ["Name", "Preis", "Fläche(m²)", "Straße", "Zimmer", "Ort"],
        )
        self.assertEqual(
            self.scraper.values,
            ["Test Name", 123.45, 100.0, "Test Street", 3.0, "12345 Test City"],
        )

        # Edge case: Preis has no numbers in it, value should be None
        metadata.find = (
            lambda tag, class_=None: MockTag("No numbers")
            if tag == "strong"
            else MockTag("Test Name")
        )
        self.scraper.keys = []
        self.scraper.values = []
        self.scraper.process_metadata(metadata)
        self.assertEqual(
            self.scraper.keys, ["Name", "Fläche(m²)", "Straße", "Zimmer", "Ort"]
        )
        self.assertEqual(
            self.scraper.values,
            ["Test Name", 100.0, "Test Street", 3.0, "12345 Test City"],
        )

        metadata.find = (
            lambda tag, class_=None: MockTag("123,45 €")
            if tag == "strong"
            else MockTag("Test Name")
        )

        # Edge case: Fläche(m²) has no numbers in it, value should be None
        metadata.find_all = lambda tag: [
            MockTag("No numbers"),
            MockTag("3"),
            MockTag("Test Street"),
            MockTag("12345 Test City"),
        ]
        self.scraper.keys = []
        self.scraper.values = []
        self.scraper.process_metadata(metadata)
        self.assertEqual(
            self.scraper.keys, ["Name", "Preis", "Straße", "Zimmer", "Ort"]
        )
        self.assertEqual(
            self.scraper.values,
            ["Test Name", 123.45, "Test Street", 3.0, "12345 Test City"],
        )

        # Edge case: Zimmer has no numbers in it, value should be None
        metadata.find_all = lambda tag: [
            MockTag("100,00 m²"),
            MockTag("No numbers"),
            MockTag("Test Street"),
            MockTag("12345 Test City"),
        ]
        self.scraper.keys = []
        self.scraper.values = []
        self.scraper.process_metadata(metadata)
        self.assertEqual(
            self.scraper.keys, ["Name", "Preis", "Fläche(m²)", "Straße", "Ort"]
        )
        self.assertEqual(
            self.scraper.values,
            ["Test Name", 123.45, 100.0, "Test Street", "12345 Test City"],
        )

        # Edge case: Straße nicht freigegeben, value should be None
        metadata.find_all = lambda tag: [
            MockTag("100,00 m²"),
            MockTag("3"),
            MockTag("Straße nicht freigegeben"),
            MockTag("12345 Test City"),
        ]
        self.scraper.keys = []
        self.scraper.values = []
        self.scraper.process_metadata(metadata)
        self.assertEqual(
            self.scraper.keys, ["Name", "Preis", "Fläche(m²)", "Zimmer", "Ort"]
        )
        self.assertEqual(
            self.scraper.values, ["Test Name", 123.45, 100.0, 3.0, "12345 Test City"]
        )

    def process_information_test(self, process_function):
        # Mock tag object
        class MockTag:
            def __init__(self, text):
                self.text = text

        # Mock information object
        class MockInformation:
            def find_all(self, tag):
                return [
                    MockTag("Key1"),
                    MockTag("Value1"),
                    MockTag("Key2"),
                    MockTag("Value2"),
                ]

        information = MockInformation()
        process_function(information)
        self.assertEqual(self.scraper.keys, ["Key1", "Key2"])
        self.assertEqual(self.scraper.values, ["Value1", "Value2"])

        # Edge case: information is None
        self.scraper.keys = []
        self.scraper.values = []
        process_function(None)
        self.assertEqual(self.scraper.keys, [])
        self.assertEqual(self.scraper.values, [])

    def test_process_estate_information(self):
        self.process_information_test(self.scraper.process_estate_information)

    def test_process_energy_information(self):
        self.process_information_test(self.scraper.process_energy_information)

    def test_process_price_information(self):
        self.process_information_test(self.scraper.process_price_information)

    def test_to_dataframe(self):
        # Mock data_dict
        self.scraper.data_dict = {
            "Name": ["Test Name 1", "Test Name 2"],
            "Preis": [123.45, 678.90],
            "Fläche(m²)": [100.0, 200.0],
            "Straße": ["Test Street 1", "Test Street 2"],
        }

        df = self.scraper.to_dataframe()
        expected_df = pd.DataFrame(
            {
                "Name": ["Test Name 1", "Test Name 2"],
                "Preis": [123.45, 678.90],
                "Fläche(m²)": [100.0, 200.0],
                "Straße": ["Test Street 1", "Test Street 2"],
            }
        )

        pd.testing.assert_frame_equal(df, expected_df)

    @patch.object(ImmoweltScraper, "get_page")
    @patch.object(ImmoweltScraper, "get_data")
    def test_scrape(self, mock_get_data, mock_get_page):
        mock_get_page.return_value = MagicMock()
        self.scraper.scrape()
        self.assertEqual(mock_get_page.call_count, self.scraper.num_pages)
        self.assertEqual(mock_get_data.call_count, self.scraper.num_pages)


if __name__ == "__main__":
    unittest.main()
