#!/usr/bin/env python3
"""Experiment 4.1: Multithreaded Statistical Reduction Workers."""
import threading

DATA = [88, 74, 93, 67, 81, 95, 79, 84, 91]
RESULTS = {}

def calc_avg():
    RESULTS["avg"] = sum(DATA) / len(DATA)

def calc_min():
    RESULTS["min"] = min(DATA)

def calc_max():
    RESULTS["max"] = max(DATA)

if __name__ == "__main__":
    workers = [
        threading.Thread(target=calc_avg, name="MeanThread"),
        threading.Thread(target=calc_min, name="MinThread"),
        threading.Thread(target=calc_max, name="MaxThread"),
    ]
    for t in workers:
        t.start()
    for t in workers:
        t.join()

    print(f"Input Dataset     : {DATA}")
    print(f"The average value : {RESULTS['avg']:.2f}")
    print(f"The minimum value : {RESULTS['min']}")
    print(f"The maximum value : {RESULTS['max']}")
