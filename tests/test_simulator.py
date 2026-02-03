import unittest
import pandas as pd
from hpa.spec import HPASpec
from hpa.simulator import simulate_hpa

class TestHPASimulator(unittest.TestCase):
    def test_scale_up_immediate(self):
        """Requirement 1: Scale-up should happen immediately when CPU exceeds target."""
        spec = HPASpec(min_replicas=1, max_replicas=10, target_utilization=50)
        metrics = pd.DataFrame({
            'timestamp': pd.to_datetime(['2024-01-01T10:00:00', '2024-01-01T10:01:00']),
            'cpu_utilization': [50, 200]
        })
        # 1. 50% -> 1 replica
        # 2. 200% -> 4 replicas. Should be immediate.
        results = simulate_hpa(metrics, spec)
        self.assertEqual(results.iloc[1]['simulated_replicas'], 4)

    def test_scale_down_stabilization(self):
        """Requirement 2: Scale-down should NOT happen if a higher desired replica appears within the stabilization window."""
        spec = HPASpec(min_replicas=1, max_replicas=10, target_utilization=50) # Defualt window 300s
        metrics = pd.DataFrame({
            'timestamp': pd.to_datetime(['2024-01-01T10:00:00', '2024-01-01T10:01:00', '2024-01-01T10:02:00']),
            'cpu_utilization': [50, 100, 10]
        })
        
        results = simulate_hpa(metrics, spec)
        
        # 1. 10:00 -> 50% -> 1 replica
        self.assertEqual(results.iloc[0]['simulated_replicas'], 1)
        # 2. 10:01 -> 100% -> 2 replicas (High watermark)
        self.assertEqual(results.iloc[1]['simulated_replicas'], 2)
        # 3. 10:02 -> 10% -> 1 replica raw.
        # But window [09:57, 10:02] contains the rec of 2 from 10:01.
        # So must stay at 2.
        self.assertEqual(results.iloc[2]['simulated_replicas'], 2)

    def test_scale_down_after_window_expiry(self):
        """Requirement 3: Scale-down should happen only after the stabilization window has fully elapsed."""
        spec = HPASpec(min_replicas=1, max_replicas=10, target_utilization=50) # Window 300s
        
        timestamps = [
            '2024-01-01T10:00:00', # Baseline
            '2024-01-01T10:01:00', # Spike to 2 replicas
            '2024-01-01T10:07:00'  # Dip 6 mins later (outside window)
        ]
        metrics = pd.DataFrame({
            'timestamp': pd.to_datetime(timestamps),
            'cpu_utilization': [50, 100, 10]
        })
        
        results = simulate_hpa(metrics, spec)
        
        # At 10:07, window is [10:02, 10:07].
        # The spike event at 10:01 is outside the window.
        # Max in window is determined by recent values.
        # The only value IN the window is the current one at 10:07 (rec 1).
        # So stabilized rec is 1. We scale down.
        self.assertEqual(results.iloc[2]['simulated_replicas'], 1)

if __name__ == "__main__":
    unittest.main()
