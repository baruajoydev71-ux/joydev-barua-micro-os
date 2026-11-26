#!/usr/bin/env python3
"""Experiment 9.1: Fixed Partition Allocation & Internal Fragmentation."""

def simulate_fixed_partitions():
    partitions = [100, 250, 60, 400, 200]
    requests = [80, 220, 45, 190, 450]
    used = [False] * len(partitions)
    total_frag = 0

    print("Fixed Partition Allocation Trace (KB):")
    for idx, req in enumerate(requests, start=1):
        placed = False
        for i, part in enumerate(partitions):
            if not used[i] and part >= req:
                used[i] = True
                frag = part - req
                total_frag += frag
                print(f"  P{idx} ({req:3d} KB) -> Partition {i} ({part:3d} KB) | Internal Frag = {frag:3d} KB")
                placed = True
                break
        if not placed:
            print(f"  P{idx} ({req:3d} KB) -> REJECTED (Exceeds largest free partition)")
    print(f"Total Internal Fragmentation: {total_frag} KB")

if __name__ == "__main__":
    simulate_fixed_partitions()
