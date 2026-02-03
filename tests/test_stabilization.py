import unittest
import pandas as pd
from hpa.stabilization import StabilizationWindow

class TestStabilizationWindow(unittest.TestCase):
    def test_basic_window_behavior(self):
        window = StabilizationWindow()
        
        # t0: 5 replicas
        t0 = pd.Timestamp("2024-01-01 10:00:00")
        window.record_recommendation(t0, 5)
        
        # Verify: max in window is 5
        rec = window.get_stabilized_recommendation(t0, window_seconds=300)
        self.assertEqual(rec, 5)

    def test_scale_down_delay(self):
        window = StabilizationWindow()
        
        # t0: 10 replicas
        t0 = pd.Timestamp("2024-01-01 10:00:00")
        window.record_recommendation(t0, 10)
        
        # t1: 2 replicas (after 2 minutes)
        t1 = t0 + pd.Timedelta(minutes=2)
        window.record_recommendation(t1, 2)
        
        # Check at t1 with 5 min window
        # Window [09:57, 10:02]. Contains (t0, 10), (t1, 2). Max is 10.
        rec = window.get_stabilized_recommendation(t1, window_seconds=300)
        self.assertEqual(rec, 10) # Should NOT scale down yet

    def test_scale_down_after_window(self):
        window = StabilizationWindow()
        
        # t0: 10 replicas
        t0 = pd.Timestamp("2024-01-01 10:00:00")
        window.record_recommendation(t0, 10)
        
        # t1: 2 replicas (after 6 minutes)
        t1 = t0 + pd.Timedelta(minutes=6)
        window.record_recommendation(t1, 2)
        
        # Check at t1 with 5 min window
        # Window [10:01, 10:06]. t0 (10:00) is OUTSIDE. Only (t1, 2) inside.
        rec = window.get_stabilized_recommendation(t1, window_seconds=300)
        self.assertEqual(rec, 2) # Should scale down now

    def test_scale_up_immediate(self):
        window = StabilizationWindow()
        
        # t0: 2 replicas
        t0 = pd.Timestamp("2024-01-01 10:00:00")
        window.record_recommendation(t0, 2)
        
        # t1: 10 replicas (after 1 minute)
        t1 = t0 + pd.Timedelta(minutes=1)
        window.record_recommendation(t1, 10)
        
        # Check at t1 with 5 min window
        # Window [09:56, 10:01]. Contains (t0, 2), (t1, 10). Max is 10.
        rec = window.get_stabilized_recommendation(t1, window_seconds=300)
        self.assertEqual(rec, 10) # Should scale up immediately

if __name__ == "__main__":
    unittest.main()
