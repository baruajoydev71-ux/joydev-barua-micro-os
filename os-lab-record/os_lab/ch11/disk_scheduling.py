#!/usr/bin/env python3
"""Experiment 11.1: Disk Arm Scheduling Comparison (FCFS, SSTF, SCAN, C-SCAN, LOOK)."""

REQUESTS = [98, 183, 37, 122, 14, 124, 65, 67]
START_HEAD = 53
MAX_CYLINDER = 199

def total_seek(order):
    return sum(abs(order[i] - order[i - 1]) for i in range(1, len(order)))

def run_fcfs(reqs, head):
    return [head] + list(reqs)

def run_sstf(reqs, head):
    pending, cur, order = list(reqs), head, [head]
    while pending:
        nxt = min(pending, key=lambda c: abs(c - cur))
        pending.remove(nxt)
        order.append(nxt)
        cur = nxt
    return order

def run_scan(reqs, head, max_cyl):
    left = sorted(r for r in reqs if r < head)
    right = sorted(r for r in reqs if r >= head)
    return [head] + right + [max_cyl] + list(reversed(left))

def run_cscan(reqs, head, max_cyl):
    left = sorted(r for r in reqs if r < head)
    right = sorted(r for r in reqs if r >= head)
    return [head] + right + [max_cyl, 0] + left

def run_look(reqs, head):
    left = sorted(r for r in reqs if r < head)
    right = sorted(r for r in reqs if r >= head)
    return [head] + right + list(reversed(left))

if __name__ == "__main__":
    print(f"Initial Head: {START_HEAD} | Cylinders: 0..{MAX_CYLINDER}")
    print(f"Request Queue: {REQUESTS}\n")
    policies = [
        ("FCFS", run_fcfs(REQUESTS, START_HEAD)),
        ("SSTF", run_sstf(REQUESTS, START_HEAD)),
        ("SCAN (Up)", run_scan(REQUESTS, START_HEAD, MAX_CYLINDER)),
        ("C-SCAN", run_cscan(REQUESTS, START_HEAD, MAX_CYLINDER)),
        ("LOOK (Up)", run_look(REQUESTS, START_HEAD)),
    ]
    print(f"{'Policy':<11} | {'Total Seek':>10} | Head Traversal Order")
    print("-" * 68)
    for name, seq in policies:
        print(f"{name:<11} | {total_seek(seq):>10} | {' -> '.join(map(str, seq))}")
