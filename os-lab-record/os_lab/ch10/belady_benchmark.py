#!/usr/bin/env python3
"""Experiment 10.4: Live Comparative Benchmark & Belady's Anomaly Proof."""

ANOMALY_STR = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

def faults_fifo(refs, cap):
    f, cnt = [], 0
    for p in refs:
        if p not in f:
            cnt += 1
            if len(f) == cap: f.pop(0)
            f.append(p)
    return cnt

def faults_lru(refs, cap):
    f, seen, cnt = [], {}, 0
    for t, p in enumerate(refs):
        if p not in f:
            cnt += 1
            if len(f) == cap: f.remove(min(f, key=lambda x: seen[x]))
            f.append(p)
        seen[p] = t
    return cnt

def faults_opt(refs, cap):
    f, cnt = [], 0
    for i, p in enumerate(refs):
        if p not in f:
            cnt += 1
            if len(f) == cap:
                nxt = {x: (refs[i+1:].index(x) if x in refs[i+1:] else 999) for x in f}
                f.remove(max(nxt, key=nxt.get))
            f.append(p)
    return cnt

if __name__ == "__main__":
    print(f"Reference String: {ANOMALY_STR}\n")
    print(f"{'Algorithm':<12} | {'3 Frames':>8} | {'4 Frames':>8} | Belady's Anomaly?")
    print("-" * 56)
    for name, fn in [("FIFO", faults_fifo), ("LRU", faults_lru), ("Optimal", faults_opt)]:
        f3, f4 = fn(ANOMALY_STR, 3), fn(ANOMALY_STR, 4)
        status = "YES (Anomaly Observed!)" if f4 > f3 else "NO  (Stack Property)"
        print(f"{name:<12} | {f3:>8} | {f4:>8} | {status}")
