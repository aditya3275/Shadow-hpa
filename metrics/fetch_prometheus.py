import requests
import pandas as pd
import argparse
import time
from datetime import datetime, timedelta

def fetch_prometheus_metrics(url, query, start_time, end_time, step='1m'):
    """
    Queries Prometheus for a range of data.
    """
    api_url = f"{url}/api/v1/query_range"
    
    # Convert datetimes to timestamps
    start_ts = start_time.timestamp()
    end_ts = end_time.timestamp()
    
    params = {
        'query': query,
        'start': start_ts,
        'end': end_ts,
        'step': step
    }
    
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if data['status'] != 'success':
        raise ValueError(f"Prometheus query failed: {data}")
    
    results = data['data']['result']
    if not results:
        print("No data found for query.")
        return pd.DataFrame()
        
    # Assuming single time series result for HPA simulation
    # If multiple, we might need to handle specific series selection.
    # For now, take the first result.
    metric_data = results[0]['values']
    
    df = pd.DataFrame(metric_data, columns=['timestamp', 'cpu_utilization'])
    
    # Convert timestamp (seconds) to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    
    # Convert value to float
    df['cpu_utilization'] = df['cpu_utilization'].astype(float)
    
    return df

def parse_relative_time(duration_str):
    """Parses simple relative time strings like '1h', '30m'."""
    unit = duration_str[-1]
    value = int(duration_str[:-1])
    
    if unit == 'h':
        return timedelta(hours=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        raise ValueError("Unknown time unit. Use h, m, or d.")

def main():
    parser = argparse.ArgumentParser(description="Fetch metrics from Prometheus")
    parser.add_argument("--url", default="http://localhost:9090", help="Prometheus URL")
    parser.add_argument("--query", required=True, help="PromQL query (e.g. sum(rate(container_cpu_usage_seconds_total...)))")
    parser.add_argument("--duration", default="1h", help="Lookback duration (e.g. 1h, 30m)")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--step", default="1m", help="Query resolution step")
    
    args = parser.parse_args()
    
    end_time = datetime.now()
    start_time = end_time - parse_relative_time(args.duration)
    
    print(f"Fetching metrics from {args.url}...")
    print(f"Query: {args.query}")
    print(f"Time Range: {start_time} to {end_time}")
    
    try:
        df = fetch_prometheus_metrics(args.url, args.query, start_time, end_time, args.step)
        
        if not df.empty:
            df.to_csv(args.output, index=False)
            print(f"Successfully saved {len(df)} records to {args.output}")
            print(df.head())
        else:
            print("No data retrieved.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
