#!/usr/bin/env python3
"""Experiment 8.1: Dijkstra's Banker's Algorithm Safety Check."""

def check_safety(avail, max_claim, alloc):
    n_procs, n_res = len(alloc), len(avail)
    need = [[max_claim[i][j] - alloc[i][j] for j in range(n_res)] for i in range(n_procs)]
    work = list(avail)
    done = [False] * n_procs
    seq = []

    while len(seq) < n_procs:
        progressed = False
        for i in range(n_procs):
            if not done[i] and all(need[i][j] <= work[j] for j in range(n_res)):
                for j in range(n_res):
                    work[j] += alloc[i][j]
                done[i] = True
                seq.append(f"P{i}")
                progressed = True
                break
        if not progressed:
            return False, []
    return True, seq

if __name__ == "__main__":
    available = [3, 3, 2]
    allocation = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
    maximum = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
    safe, sequence = check_safety(available, maximum, allocation)
    print(f"System Safety Status : {'SAFE' if safe else 'UNSAFE'}")
    print("Safe Sequence        :", " -> ".join(sequence))
