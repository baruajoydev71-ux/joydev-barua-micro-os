#!/usr/bin/env python3
"""Experiment 9.2: First-Fit, Best-Fit & Worst-Fit Dynamic Allocation."""

HOLES = [100, 500, 200, 300, 600]
PROCS = [212, 417, 112, 426]

def run_policy(name, selector):
    holes = list(HOLES)
    placed_count = 0
    print(f"--- {name} ---")
    for idx, p in enumerate(PROCS, start=1):
        cands = [(i, h) for i, h in enumerate(holes) if h >= p]
        if cands:
            slot, orig = selector(cands)
            holes[slot] -= p
            placed_count += 1
            print(f"  P{idx} ({p} KB) -> Hole #{slot} (was {orig} KB, rem {holes[slot]} KB)")
        else:
            print(f"  P{idx} ({p} KB) -> NOT ALLOCATED (External Fragmentation)")
    print(f"  Summary: {placed_count}/{len(PROCS)} allocated | Remaining holes: {holes}\n")

if __name__ == "__main__":
    run_policy("First-Fit", lambda c: c[0])
    run_policy("Best-Fit",  lambda c: min(c, key=lambda x: x[1]))
    run_policy("Worst-Fit", lambda c: max(c, key=lambda x: x[1]))
