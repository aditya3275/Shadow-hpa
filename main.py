"""
Shadow HPA CLI.

This entry point allows users to replay historical CPU metrics
through a simulated Kubernetes HPA control loop and analyze
cost and reliability trade-offs before touching production.
"""


import argparse
import sys
import pandas as pd
from hpa.spec import HPASpec
from hpa.simulator import simulate_hpa
from metrics.loader import load_cpu_metrics
from hpa.regret import (
    calculate_cpu_hours, 
    calculate_wasted_resources, 
    calculate_under_provisioning_risk
)

def main():
    parser = argparse.ArgumentParser(description="Shadow HPA Simulator CLI")
    
    parser.add_argument("--csv", required=True, help="Path to historical CPU metrics CSV")
    parser.add_argument("--min-replicas", type=int, default=1, help="Minimum replicas (default: 1)")
    parser.add_argument("--max-replicas", type=int, default=10, help="Maximum replicas (default: 10)")
    parser.add_argument("--target", type=int, required=True, help="Target CPU utilization percentage")
    parser.add_argument("--scale-down-window", type=int, default=300, help="Scale-down stabilization window in seconds (default: 300)")
    
    args = parser.parse_args()
    
    try:
        print(f"Loading metrics from {args.csv}...")
        metrics = load_cpu_metrics(args.csv)
        
        spec = HPASpec(
            min_replicas=args.min_replicas,
            max_replicas=args.max_replicas,
            target_utilization=args.target,
            scale_down_stabilization_window_seconds=args.scale_down_window
        )
        
        print(f"Running simulation with target {args.target}%...")
        results = simulate_hpa(metrics, spec)
        
        # Calculate Metrics
        cost = calculate_cpu_hours(results)
        risk = calculate_under_provisioning_risk(results, metrics, args.target)
        
        waste = "N/A"
        if 'replicas' in metrics.columns:
            waste_val = calculate_wasted_resources(metrics, results)
            waste = f"{waste_val:.2f} replica-minutes"
        

        # The CLI intentionally outputs human-readable summaries
        # so engineers can reason about scaling behavior quickly.

        print("\n=== Shadow HPA Simulation Results ===")
        print(f"Total CPU Cost:            {cost:.4f} CPU-hours")
        print(f"Under-Provisioning Risk:   {risk:.2f} minutes")
        print(f"Scale-Up Regret (Waste):   {waste}")
        print("=====================================")
        
        # Optional: Save results? 
        # For now just stdout summary.
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
