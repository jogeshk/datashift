import unittest
import json
import pathlib
import os
from datashift.converter import convert

class TestDataShiftConverter(unittest.TestCase):

    def setUp(self):
        """Runs automatically before every single test case to create dummy data files."""
        self.test_json_path = "test_input.json"
        self.test_csv_path = "test_output.csv"
        
        self.sample_data = {"name": "Jogesh K", "role": "Developer"}
        with open(self.test_json_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_data, f)

    def tearDown(self):
        """Runs automatically after tests finish to wipe temporary files from your laptop."""
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)

    def test_json_to_csv_conversion(self):
        """Verifies if JSON data successfully morphs into flat CSV data."""
        convert(self.test_json_path, self.test_csv_path)
        self.assertTrue(pathlib.Path(self.test_csv_path).exists())

    def test_missing_file_error(self):
        """Ensures your engine safely handles missing targets instead of throwing a generic crash."""
        with self.assertRaises(FileNotFoundError):
            convert("non_existent_file.json", "output.csv")

if __name__ == "__main__":
    unittest.main()
    