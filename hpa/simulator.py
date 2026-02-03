"""
Core simulation logic for the Shadow Horizontal Pod Autoscaler.

This module replicates the Kubernetes HPA scaling algorithm in a deterministic,
side-effect-free manner, suitable for historical metrics replay.
"""

"""
This module implements the core Kubernetes HPA replica calculation
in 'shadow mode' by replaying historical CPU metrics.

Stabilization logic is intentionally excluded here to keep the
control math isolated and testable.
"""


import pandas as pd
import math
from hpa.spec import HPASpec

def simulate_hpa(metrics_df: pd.DataFrame, spec: HPASpec) -> pd.DataFrame:
    """
    Simulates HPA scaling behavior over a series of CPU metrics.
    
    The simulation follows the Kubernetes HPA formula:
    desiredReplicas = ceil[currentReplicas * (currentMetricValue / desiredMetricValue)]
    
    Args:
        metrics_df (pd.DataFrame): DataFrame with 'timestamp' and 'cpu_utilization'.
        spec (HPASpec): The HPA configuration.
        
    Returns:
        pd.DataFrame: A DataFrame containing 'timestamp' and 'simulated_replicas'.
    """
    results = []
    current_replicas = spec.min_replicas
    
    for _, row in metrics_df.iterrows():
        timestamp = row['timestamp']
        current_cpu = row['cpu_utilization']
        
        # 1. Apply HPA formula
        # ratio = currentMetricValue / desiredMetricValue
        ratio = current_cpu / spec.target_utilization
        
        # 2. Apply tolerance
        # If the ratio is within tolerance, we keep the current replicas.
        # Kubernetes uses: if abs(1 - ratio) <= tolerance, then ratio = 1
        if abs(1 - ratio) <= spec.tolerance:
            desired_replicas = current_replicas
        else:
            desired_replicas = math.ceil(current_replicas * ratio)

         # Kubernetes ignores minor metric fluctuations within tolerance to avoid unnecessary scaling events.   
        # 3. Enforce min/max replicas
        desired_replicas = max(spec.min_replicas, min(spec.max_replicas, desired_replicas))
        
        # Record results
        results.append({
            'timestamp': timestamp,
            'simulated_replicas': desired_replicas
        })
        
        # For this version (no stabilization), the next step's current_replicas 
        # is the current step's desired_replicas.
        current_replicas = desired_replicas
        
    return pd.DataFrame(results)
