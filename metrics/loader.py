"""
This module ingests historical CPU metrics and prepares them for replay.

Metrics are treated as immutable historical truth.
No real-time assumptions are made — time always moves forward.
"""





import pandas as pd
import os

def load_cpu_metrics(file_path: str) -> pd.DataFrame:
    """
    Loads historical CPU utilization data from a CSV file.
    
    The CSV must contain 'timestamp' (ISO 8601) and 'cpu_utilization' (percentage) columns.
    The data will be sorted chronologically by timestamp.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: A pandas DataFrame with 'timestamp' as datetime and 'cpu_utilization'.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing or data is invalid.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    required_columns = {'timestamp', 'cpu_utilization'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns in CSV: {missing_columns}")
    
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    except Exception as e:
        raise ValueError(f"Failed to parse timestamps: {e}")
    
    # Sort chronologically
    df = df.sort_values(by='timestamp').reset_index(drop=True)
    
    
    return df
    # Data is intentionally sorted to ensure deterministic simulation behavior.

