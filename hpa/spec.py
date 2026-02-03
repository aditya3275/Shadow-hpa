"""
HPASpec represents an autoscaling policy, not behavior.

It is intentionally immutable so that scaling simulations are deterministic
and reproducible across historical replays.
"""



from dataclasses import dataclass

@dataclass(frozen=True)
class HPASpec:
    """
    Models a Kubernetes Horizontal Pod Autoscaler configuration.
    
    Attributes:
        min_replicas (int): Minimum number of replicas. Must be > 0.
        max_replicas (int): Maximum number of replicas. Must be >= min_replicas.
        target_utilization (int): Target CPU utilization percentage (e.g., 70). Must be between 1 and 100.
        scale_down_stabilization_window_seconds (int): Window for cooling down after a scale down. Default 300.
        tolerance (float): The threshold for initiating a scaling operation. Default 0.1. Must be between 0 and 1.
    """
    min_replicas: int
    max_replicas: int
    target_utilization: int
    scale_down_stabilization_window_seconds: int = 300
    tolerance: float = 0.1

    def __post_init__(self):
        """
        Validate the fields after initialization.
        """
        if self.min_replicas <= 0:
            raise ValueError(f"min_replicas must be greater than 0, got {self.min_replicas}")
        
        if self.max_replicas < self.min_replicas:
            raise ValueError(f"max_replicas ({self.max_replicas}) must be greater than or equal to min_replicas ({self.min_replicas})")
        
        if not (1 <= self.target_utilization <= 100):
            raise ValueError(f"target_utilization must be between 1 and 100, got {self.target_utilization}")
        
        if not (0 <= self.tolerance <= 1):
            raise ValueError(f"tolerance must be between 0 and 1, got {self.tolerance}")
