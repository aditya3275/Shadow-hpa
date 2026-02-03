import unittest
import pandas as pd
import matplotlib.pyplot as plt
from visualize.plot import plot_simulation_results

class TestPlotting(unittest.TestCase):
    def test_plot_execution(self):
        # Verify that plot_simulation_results runs without error
        # and returns a Figure object.
        
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(['2024-01-01 10:00', '2024-01-01 10:05']),
            'cpu_utilization': [50, 80],
            'simulated_replicas': [1, 2]
        })
        
        fig = plot_simulation_results(df)
        self.assertIsInstance(fig, plt.Figure)
        
        # Cleanup
        plt.close(fig)

    def test_plot_empty_data(self):
        df = pd.DataFrame()
        with self.assertRaises(ValueError):
            plot_simulation_results(df)

if __name__ == "__main__":
    unittest.main()
