import unittest
from hpa.spec import HPASpec

class TestHPASpec(unittest.TestCase):
    def test_hpa_spec_valid_initialization(self):
        spec = HPASpec(
            min_replicas=2,
            max_replicas=10,
            target_utilization=70,
            scale_down_stabilization_window_seconds=600,
            tolerance=0.05
        )
        self.assertEqual(spec.min_replicas, 2)
        self.assertEqual(spec.max_replicas, 10)
        self.assertEqual(spec.target_utilization, 70)
        self.assertEqual(spec.scale_down_stabilization_window_seconds, 600)
        self.assertEqual(spec.tolerance, 0.05)

    def test_hpa_spec_default_values(self):
        spec = HPASpec(
            min_replicas=1,
            max_replicas=5,
            target_utilization=50
        )
        self.assertEqual(spec.scale_down_stabilization_window_seconds, 300)
        self.assertEqual(spec.tolerance, 0.1)

    def test_hpa_spec_immutability(self):
        spec = HPASpec(min_replicas=1, max_replicas=5, target_utilization=50)
        with self.assertRaises(Exception): # Frozen dataclass raises FrozenInstanceError
            spec.min_replicas = 2

    def test_hpa_spec_validation_min_replicas(self):
        with self.assertRaisesRegex(ValueError, "min_replicas must be greater than 0"):
            HPASpec(min_replicas=0, max_replicas=10, target_utilization=70)

    def test_hpa_spec_validation_max_replicas(self):
        with self.assertRaisesRegex(ValueError, r"max_replicas \(.*\) must be greater than or equal to min_replicas"):
            HPASpec(min_replicas=5, max_replicas=2, target_utilization=70)

    def test_hpa_spec_validation_target_utilization_low(self):
        with self.assertRaisesRegex(ValueError, "target_utilization must be between 1 and 100"):
            HPASpec(min_replicas=1, max_replicas=10, target_utilization=0)

    def test_hpa_spec_validation_target_utilization_high(self):
        with self.assertRaisesRegex(ValueError, "target_utilization must be between 1 and 100"):
            HPASpec(min_replicas=1, max_replicas=10, target_utilization=101)

    def test_hpa_spec_validation_tolerance_low(self):
        with self.assertRaisesRegex(ValueError, "tolerance must be between 0 and 1"):
            HPASpec(min_replicas=1, max_replicas=10, target_utilization=70, tolerance=-0.1)

    def test_hpa_spec_validation_tolerance_high(self):
        with self.assertRaisesRegex(ValueError, "tolerance must be between 0 and 1"):
            HPASpec(min_replicas=1, max_replicas=10, target_utilization=70, tolerance=1.1)

if __name__ == "__main__":
    unittest.main()
