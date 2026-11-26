#!/usr/bin/env python3
"""Experiment 5.1: FCFS vs Non-Preemptive SJF CPU Scheduling."""

PROCESSES = [
    {"pid": "P1", "burst": 7},
    {"pid": "P2", "burst": 4},
    {"pid": "P3", "burst": 9},
    {"pid": "P4", "burst": 2},
]

def evaluate(title, ordered_procs):
    clock, sum_wt, sum_tat = 0, 0, 0
    print(f"--- {title} ---")
    for p in ordered_procs:
        wt = clock
        tat = wt + p["burst"]
        clock += p["burst"]
        sum_wt += wt
        sum_tat += tat
        print(f"  {p['pid']}: Burst={p['burst']:2d} | WT={wt:2d} | TAT={tat:2d}")
    n = len(ordered_procs)
    print(f"  Average WT = {sum_wt / n:.2f} ms | Average TAT = {sum_tat / n:.2f} ms\n")

if __name__ == "__main__":
    evaluate("FCFS Scheduling", PROCESSES)
    evaluate("SJF Scheduling (Optimal Non-Preemptive)", sorted(PROCESSES, key=lambda p: p["burst"]))
