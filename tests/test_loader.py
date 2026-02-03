import unittest
import pandas as pd
import os
import tempfile
from metrics.loader import load_cpu_metrics

class TestMetricsLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.test_dir.name, "metrics.csv")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_metrics_success(self):
        # Create a valid CSV file
        data = {
            'timestamp': ['2026-02-03T22:00:00Z', '2026-02-03T21:00:00Z'], # Unsorted
            'cpu_utilization': [75, 60]
        }
        pd.DataFrame(data).to_csv(self.csv_path, index=False)
        
        df = load_cpu_metrics(self.csv_path)
        
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['cpu_utilization'], 60) # Should be sorted
        self.assertEqual(df.iloc[1]['cpu_utilization'], 75)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['timestamp']))

    def test_load_metrics_missing_column(self):
        # Missing cpu_utilization
        data = {'timestamp': ['2026-02-03T22:00:00Z']}
        pd.DataFrame(data).to_csv(self.csv_path, index=False)
        
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            load_cpu_metrics(self.csv_path)

    def test_load_metrics_invalid_timestamp(self):
        data = {
            'timestamp': ['invalid-date'],
            'cpu_utilization': [50]
        }
        pd.DataFrame(data).to_csv(self.csv_path, index=False)
        
        with self.assertRaisesRegex(ValueError, "Failed to parse timestamps"):
            load_cpu_metrics(self.csv_path)

    def test_load_metrics_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_cpu_metrics("non_existent.csv")

if __name__ == "__main__":
    unittest.main()
