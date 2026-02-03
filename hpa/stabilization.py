"""
Scale-down stabilization prevents replica flapping by delaying scale-down
until the workload has remained consistently low for a fixed window.

This mirrors Kubernetes HPA's conservative scale-down behavior.
"""



from dataclasses import dataclass
from collections import deque
import pandas as pd
from typing import List, Tuple

class StabilizationWindow:
    """
    Implements a rolling window of recommendation history to stabilize scale-down decisions.
    
    This mirrors the Kubernetes HPA stabilization behavior: it calculates the
    stabilized recommendation as the maximum recommendation observed within the 
    sliding window ending at the current timestamp.
    """
    def __init__(self):
        # Stores tuples of (timestamp, desired_replicas)
        # We use a deque for efficient popping from the left if we wanted to prune,
        # though for simple simulation a list is also fine.
        self.history: deque[Tuple[pd.Timestamp, int]] = deque()

    def record_recommendation(self, timestamp: pd.Timestamp, replicas: int):
        """
        Records a calculated desired replica count.
        
        Args:
            timestamp (pd.Timestamp): The time of the recommendation.
            replicas (int): The calculated desired replica count.
        """
        # Ensure timestamps are strictly increasing is not strictly required by logic 
        # but expected in simulation.
        self.history.append((timestamp, replicas))

    def get_stabilized_recommendation(self, current_timestamp: pd.Timestamp, window_seconds: int) -> int:
        """
        Calculates the stabilized recommendation based on the history window.
        
        The stabilized recommendation is the MAXIMUM value found in the window 
        [current_timestamp - window_seconds, current_timestamp].
        
        Args:
            current_timestamp (pd.Timestamp): The current time.
            window_seconds (int): The length of the stabilization window in seconds.
            
        Returns:
            int: The stabilized desired replica count. Returns 0 if no history exists (unlikely in flow).
        """
        if not self.history:
            return 0
            
        cutoff = current_timestamp - pd.Timedelta(seconds=window_seconds)
        
        # We consider all recommendations that happened after the cutoff (inclusive-ish) 
        # and up to current_timestamp.
        # Since history is appended chronologically, we could optimize search, 
        # but linear scan is fine for typical window sizes.
        
        max_replicas = 0
        found_in_window = False
        # If any recent desired value suggests higher capacity,
        # we block scale-down to avoid premature contraction.

        for ts, replicas in reversed(self.history):
            if ts < cutoff:
                break
            if ts <= current_timestamp:
                max_replicas = max(max_replicas, replicas)
                found_in_window = True
                
        if not found_in_window:
            # Fallback: if no recommendations in window (e.g. huge gap), 
            # arguably should return the most recent one or current?
            # For now, let's return the most recent one if it exists.
             return self.history[-1][1]

        return max_replicas
