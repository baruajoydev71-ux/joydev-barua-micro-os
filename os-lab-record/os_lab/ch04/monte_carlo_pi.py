#!/usr/bin/env python3
"""Experiment 4.2: Multithreaded Monte Carlo Approximation of Pi."""
import math
import random
import threading

TOTAL_POINTS = 400_000
NUM_THREADS = 4
hits_total = 0
lock = threading.Lock()

def worker(seed, n_points):
    global hits_total
    rng = random.Random(seed)
    local_hits = 0
    for _ in range(n_points):
        x, y = rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)
        if x * x + y * y <= 1.0:
            local_hits += 1
    with lock:
        hits_total += local_hits

if __name__ == "__main__":
    per_thread = TOTAL_POINTS // NUM_THREADS
    threads = [threading.Thread(target=worker, args=(298 + i, per_thread)) for i in range(NUM_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    pi_est = 4.0 * hits_total / TOTAL_POINTS
    print(f"Threads Launched : {NUM_THREADS}")
    print(f"Total Samples    : {TOTAL_POINTS}")
    print(f"Hits in Circle   : {hits_total}")
    print(f"Estimated Pi     : {pi_est:.6f} (Abs Error: {abs(pi_est - math.pi):.6f})")
