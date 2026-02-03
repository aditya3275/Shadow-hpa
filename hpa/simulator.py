"""
Core simulation logic for the Shadow Horizontal Pod Autoscaler.

This module replicates the Kubernetes HPA scaling algorithm in a deterministic,
side-effect-free manner, suitable for historical metrics replay.
"""

import pandas as pd
import math
from hpa.spec import HPASpec
from hpa.stabilization import StabilizationWindow

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
    stabilizer = StabilizationWindow()
    
    for _, row in metrics_df.iterrows():
        timestamp = row['timestamp']
        current_cpu = row['cpu_utilization']
        
        # 1. Apply HPA formula
        # ratio = currentMetricValue / desiredMetricValue
        ratio = current_cpu / spec.target_utilization
        
        # 2. Apply tolerance
        if abs(1 - ratio) <= spec.tolerance:
            raw_desired = current_replicas
        else:
            raw_desired = math.ceil(current_replicas * ratio)
            
        # 3. Enforce min/max replicas on the raw calculation
        raw_desired = max(spec.min_replicas, min(spec.max_replicas, raw_desired))
        
        # 4. Record recommendation for stabilization
        stabilizer.record_recommendation(timestamp, raw_desired)
        
        # 5. Determine final decision
        if raw_desired > current_replicas:
            # Scale Up: Immediate (skip stabilization for this version)
            desired_replicas = raw_desired
        else:
            # Scale Down: Stabilized
            stabilized_recommendation = stabilizer.get_stabilized_recommendation(
                timestamp, spec.scale_down_stabilization_window_seconds
            )
            # We can only scale down to the stabilized recommendation
            # (which is the max of recent recommendations)
            desired_replicas = min(current_replicas, stabilized_recommendation)
            
        # Record results
        results.append({
            'timestamp': timestamp,
            'simulated_replicas': desired_replicas
        })
        
        current_replicas = desired_replicas
        
    return pd.DataFrame(results)
