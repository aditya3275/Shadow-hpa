"""
Visualization utilities for Shadow HPA.

Graphs are designed to make autoscaling decisions explainable
by correlating CPU demand with replica changes over time.
"""



import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional

def plot_simulation_results(df: pd.DataFrame, output_path: Optional[str] = None):
    """
    Plots CPU utilization and simulated replica counts on a dual-axis graph.
    
    Args:
        df (pd.DataFrame): DataFrame containing 'timestamp', 'cpu_utilization',
                           and 'simulated_replicas'.
        output_path (Optional[str]): If provided, saves the plot to this path.
                                     Otherwise, returns the figure object.
    
    Returns:
        matplotlib.figure.Figure: The plot figure object.
    """
    if df.empty:
        raise ValueError("DataFrame is empty, cannot plot.")

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot CPU on left axis
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('CPU Utilization (%)', color=color)
    ax1.plot(df['timestamp'], df['cpu_utilization'], color=color, label='CPU Utilization')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot Replicas on right axis
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color = 'tab:orange'
    ax2.set_ylabel('Replicas', color=color)
    # Step plot is more appropriate for replicas which change discretely
    ax2.step(df['timestamp'], df['simulated_replicas'], where='post', color=color, label='Simulated Replicas')
    ax2.tick_params(axis='y', labelcolor=color)

    # Title and Layout
    plt.title('Shadow HPA Simulation Results')
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    
    # Legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    if output_path:
        plt.savefig(output_path)
    
    return fig
