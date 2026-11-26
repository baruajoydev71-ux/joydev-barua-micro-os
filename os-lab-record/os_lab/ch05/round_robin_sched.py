#!/usr/bin/env python3
"""Experiment 5.2: Preemptive Round-Robin CPU Scheduler (Quantum = 3)."""
from collections import deque

def simulate_rr(tasks, quantum=3):
    q = deque([{"pid": t["pid"], "burst": t["burst"], "rem": t["burst"]} for t in tasks])
    clock = 0
    completion = {}
    switches = 0
    print(f"Round-Robin Execution Trace (Quantum = {quantum}):")
    while q:
        p = q.popleft()
        run = min(quantum, p["rem"])
        start = clock
        clock += run
        p["rem"] -= run
        switches += 1
        print(f"  [Tick {start:2d}->{clock:2d}] {p['pid']} ran {run} units (Remaining: {p['rem']})")
        if p["rem"] > 0:
            q.append(p)
        else:
            completion[p["pid"]] = clock

    avg_tat = sum(completion.values()) / len(tasks)
    avg_wt = sum(completion[t["pid"]] - t["burst"] for t in tasks) / len(tasks)
    print(f"\nCompleted {len(tasks)} tasks in {clock} ticks | Dispatches: {switches}")
    print(f"Average WT = {avg_wt:.2f} | Average TAT = {avg_tat:.2f}")

if __name__ == "__main__":
    workload = [{"pid": "P1", "burst": 9}, {"pid": "P2", "burst": 4}, {"pid": "P3", "burst": 6}, {"pid": "P4", "burst": 3}]
    simulate_rr(workload, quantum=3)
