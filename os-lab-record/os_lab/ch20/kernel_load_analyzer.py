#!/usr/bin/env python3
"""Experiment 20.2: Linux Exponential Load Average & Live Context-Switch Benchmark."""
import math
import os
import threading
import time

def bench_context_switches(pairs=2000):
    e1, e2 = threading.Event(), threading.Event()
    def pong():
        for _ in range(pairs):
            e1.wait(); e1.clear(); e2.set()
    t = threading.Thread(target=pong)
    t.start()
    t0 = time.perf_counter()
    for _ in range(pairs):
        e1.set(); e2.wait(); e2.clear()
    dt = time.perf_counter() - t0
    t.join()
    total_sw = pairs * 2
    return total_sw, dt, (dt / total_sw) * 1e6

def simulate_linux_load(samples, dt=5.0):
    l1 = l5 = l15 = 0.0
    a1, a5, a15 = math.exp(-dt / 60), math.exp(-dt / 300), math.exp(-dt / 900)
    for n_run in samples:
        l1  = l1  * a1  + n_run * (1 - a1)
        l5  = l5  * a5  + n_run * (1 - a5)
        l15 = l15 * a15 + n_run * (1 - a15)
    return l1, l5, l15

if __name__ == "__main__":
    cores = os.cpu_count() or 1
    sw, dt, us_per_sw = bench_context_switches(2000)
    print(f"Logical CPU Cores Detected : {cores}")
    print(f"Live Context-Switch Bench  : {sw} switches in {dt*1000:.2f} ms ({us_per_sw:.2f} us/switch)")
    burst = [1, 2, 4, 6, 8, 8, 6, 4, 3, 2, 2, 1]
    l1, l5, l15 = simulate_linux_load(burst)
    print(f"Simulated 60s Burst Load   : 1m={l1:.2f} | 5m={l5:.2f} | 15m={l15:.2f}")
    print(f"Per-Core Saturation Ratio  : {l1 / cores:.2f} ({'UNDERLOADED' if l1 < cores else 'SATURATED'})")
