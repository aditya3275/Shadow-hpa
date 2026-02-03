"""
This module quantifies the cost and risk implications of autoscaling decisions.

Rather than asking 'did scaling work?',
we ask 'what did scaling cost us, and what risk did it introduce?'.
"""


"""
Utilities for analyzing the performance, cost, and regret of HPA simulations.
"""

import pandas as pd
import numpy as np

def calculate_cpu_hours(
    df_or_replicas: pd.DataFrame | list, 
    timestamps: list = None,
    replicas_col: str = 'simulated_replicas'
) -> float:
    """
    Calculates the total CPU-hours consumed based on replica counts over time.
    
    Can accept a DataFrame OR raw lists of replicas and timestamps.
    
    Args:
        df_or_replicas: DataFrame with data OR list of replica counts.
        timestamps (list, optional): List of timestamps (if df_or_replicas is a list).
        replicas_col (str): The name of the column containing replica counts (if df).
        
    Returns:
        float: Total CPU-hours.
    """
    # Handle list input
    if isinstance(df_or_replicas, list):
        if timestamps is None:
            raise ValueError("Must provide timestamps list when passing replicas as list")
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(timestamps),
            replicas_col: df_or_replicas
        })
    else:
        df = df_or_replicas

    if df.empty:
        return 0.0
    
    # Ensure time is sorted
    df = df.sort_values('timestamp')
    
    # Calculate duration between timestamps in hours
    # diff() gives difference with previous row. Shift -1 gives diff with next row.
    
    # Time diff in seconds
    time_diffs = df['timestamp'].diff().shift(-1).dt.total_seconds()
    
    # Fill the last interval with 0 (step function ends at last point)
    time_diffs = time_diffs.fillna(0)
    
    hours = time_diffs / 3600.0
    cpu_hours = (df[replicas_col] * hours).sum()
    
    return float(cpu_hours)

def calculate_wasted_resources(actual_df: pd.DataFrame, simulated_df: pd.DataFrame) -> float:
    """
    Calculates "scale-up regret": wasted replica-minutes where actual replicas > simulated replicas.
    
    This metric assumes "simulated" is the optimized/ideal state. If "actual" (historical)
    used more replicas than "simulated" (optimized), the difference is waste.
    
    Args:
        actual_df (pd.DataFrame): DataFrame with 'timestamp' and 'replicas' (or similar).
        simulated_df (pd.DataFrame): DataFrame with 'timestamp' and 'simulated_replicas'.
        
    Returns:
        float: Total wasted replica-minutes.
    """
    # Merge on timestamp
    # We assume timestamps align or we traverse common range.
    # Ideally we reindex to union of timestamps and ffill, but let's stick to simple inner join for now
    # if we assume they come from the same source metrics.
    
    # Rename columns for clarity if needed, assuming standard names
    # Let's assume actual_df has 'replicas' or we pass the col name? 
    # Requirements say "Given actual replicas vs simulated replicas".
    # Let's assume standard 'simulated_replicas' in simulated_df.
    # actual_df might need standardizing.
    
    # For simplicity, let's assume appropriate column renaming happens before or we guess.
    
    # Let's handle the merge carefully with tolerance for slight misalignments?
    # "asof" merge is strictly better for time series.
    
    merged = pd.merge_asof(
        simulated_df.sort_values('timestamp'),
        actual_df.sort_values('timestamp'),
        on='timestamp',
        direction='nearest', # Or backward?
        suffixes=('_sim', '_act')
    )
    
    # Check for replica columns
    sim_col = 'simulated_replicas'
    # Fallback for actual: try 'replicas', 'actual_replicas', or just the other non-timestamp col
    act_col = None
    for col in merged.columns:
        if col not in ['timestamp', sim_col] and 'replica' in col:
            act_col = col
            break
            
    if not act_col:
        # Fallback: looks for any numeric column from actual_df
        # This is a bit fragile, but fine for now.
        # User prompt implies "actual replicas", let's assume a column 'replicas' exists if not spec'd.
        if 'replicas' in actual_df.columns:
            act_col = 'replicas' 
        else:
             # Try finding a column that ends with _act and isn't timestamp
             candidates = [c for c in merged.columns if c.endswith('_act') and c != 'timestamp']
             if candidates:
                 act_col = candidates[0]
             else:
                 return 0.0 # Cannot determine

    # Calculate difference where Actual > Simulated
    merged['waste'] = (merged[act_col] - merged[sim_col]).clip(lower=0)
    
    # Integrate over time (in minutes)
    time_diffs = merged['timestamp'].diff().shift(-1).dt.total_seconds() / 60.0
    time_diffs = time_diffs.fillna(0)
    
    total_waste = (merged['waste'] * time_diffs).sum()
    
    return float(total_waste)

def calculate_under_provisioning_risk(
    simulation_df: pd.DataFrame, 
    metrics_df: pd.DataFrame, 
    target_utilization: float, 
    lookahead_window_minutes: int = 5
) -> float:
    """
    Calculates "scale-down regret": duration (in minutes) where the system was 
    under-provisioned (CPU > Target) shortly after a scale-down event.
    
    Args:
        simulation_df (pd.DataFrame): Result of simulate_hpa.
        metrics_df (pd.DataFrame): Raw CPU metrics.
        target_utilization (float): The HPA target (e.g. 50).
        lookahead_window_minutes (int): How long after a scale-down to check for risk.
        
    Returns:
        float: Total risk duration in minutes.
    """
    # Merge simulation and metrics
    # Use merge_asof to align cpu data with simulation steps
    merged = pd.merge_asof(
        simulation_df.sort_values('timestamp'),
        metrics_df.sort_values('timestamp'),
        on='timestamp'
    )
    
    # Identify scale-down events
    # We can use sim_df directly to find scale downs
    # But merged is fine too, provided we use metrics_df for the window lookups
    
    merged['prev_replicas'] = merged['simulated_replicas'].shift(1)
    scale_downs = merged[merged['simulated_replicas'] < merged['prev_replicas']]
    
    total_risk_duration = 0.0
    
    for _, event in scale_downs.iterrows():
        start_time = event['timestamp']
        end_time = start_time + pd.Timedelta(minutes=lookahead_window_minutes)
        
        # Look at metrics in the window (start_time, end_time]
        # CRITICAL FIX: Query metrics_df (raw data), NOT merged (which only has sim steps)
        window_metrics = metrics_df[
            (metrics_df['timestamp'] > start_time) & 
            (metrics_df['timestamp'] <= end_time)
        ].copy() # Copy to avoid SettingWithCopyWarning
        
        # Calculate duration where CPU > Target
        violations = window_metrics[window_metrics['cpu_utilization'] > target_utilization]
        
        if not violations.empty:
            # Calculate duration for each point in the window
            # We calculate diff with the NEXT point in the full window_metrics (not just violations)
            # This assumes the metric holds until the next metric point.
            
            # Recalculate diffs for the specific window slice
            # Shift -1 to get duration until next point
            time_diffs = window_metrics['timestamp'].diff().shift(-1).dt.total_seconds().fillna(0) / 60.0
            window_metrics['duration_min'] = time_diffs
            
            # Sum duration ONLY for violating rows
            risk_min = window_metrics[window_metrics['cpu_utilization'] > target_utilization]['duration_min'].sum()
            total_risk_duration += risk_min
            
    return float(total_risk_duration)

# Scale-up regret represents pure waste: capacity we paid for but did not need.
# Scale-down regret approximates reliability risk introduced by premature contraction.
