import pandas as pd
import matplotlib.pyplot as plt

# --- Analysis Configuration ---
CSV_FILE = "grpc_baseline_results.csv"

def main():
    """
    Reads the benchmark results and generates performance visualizations.
    """
    try:
        # Load the performance metrics from the CSV file
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print(f"Error: {CSV_FILE} not found. Please run the test script first.")
        return

    # Normalize timestamps to seconds relative to the start of the test
    min_time = df['Start_Time'].min()
    df['Relative_Start_Time'] = df['Start_Time'] - min_time
    
    # --- Visualization 1: Latency Scatter Plot ---
    # This plot visualizes individual request latency and identifies success/failure trends
    plt.figure(figsize=(10, 5))
    success_df = df[df['Success'] == True]
    failed_df = df[df['Success'] == False]
    
    # Plot successful requests in blue
    plt.scatter(success_df['Relative_Start_Time'], success_df['Latency_sec'], color='blue', alpha=0.6, label='Success')
    
    # Plot failed requests in red with an 'x' marker if any exist
    if not failed_df.empty:
        plt.scatter(failed_df['Relative_Start_Time'], failed_df['Latency_sec'], color='red', marker='x', label='Failed')
        
    plt.title('gRPC Print Job Latency over Time (Baseline)')
    plt.xlabel('Time since test started (seconds)')
    plt.ylabel('Latency (seconds)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('grpc_latency_scatter.png')
    print("Generated: grpc_latency_scatter.png")
    
    # --- Visualization 2: Throughput (Requests Per Second) ---
    # Group requests by the integer second they completed to measure throughput
    df['End_Time_Sec'] = (df['End_Time'] - min_time).astype(int)
    throughput_series = df.groupby('End_Time_Sec').size()
    
    plt.figure(figsize=(10, 5))
    plt.plot(throughput_series.index, throughput_series.values, color='green', marker='o', linestyle='-')
    plt.title('gRPC Throughput (Requests Completed per Second)')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Requests Completed / sec')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('grpc_throughput.png')
    print("Generated: grpc_throughput.png")

if __name__ == "__main__":
    main()
