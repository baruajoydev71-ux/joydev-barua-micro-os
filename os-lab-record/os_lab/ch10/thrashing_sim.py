#!/usr/bin/env python3
"""Experiment 10.5: Working-Set Demand & Thrashing Collapse Simulation."""

def simulate_thrashing(total_frames=10, wss_per_proc=2.5):
    print("Thrashing Simulation (Increasing Multiprogramming Degree):")
    print(f"{'Procs':>5} | {'Working-Set Sum':>15} | {'RAM Frames':>10} | {'Fault Rate':>10} | {'CPU Util':>8}")
    print("-" * 60)
    for procs in range(1, 7):
        ws_sum = procs * wss_per_proc
        if ws_sum <= total_frames:
            fault_rate = 4.5 + procs * 1.4
            cpu_util = 22.0 + procs * 15.0
        else:
            deficit = ws_sum - total_frames
            fault_rate = min(98.0, 32.0 + deficit * 18.0)
            cpu_util = max(4.0, 82.0 - deficit * 21.0)
        print(f"{procs:>5} | {ws_sum:>15.1f} | {total_frames:>10} | {fault_rate:>9.1f}% | {cpu_util:>7.1f}%")
    print("\n[ALERT] Thrashing detected once sum(WSS) > available physical frames!")

if __name__ == "__main__":
    simulate_thrashing()
