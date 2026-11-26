#!/usr/bin/env python3
"""Experiment 10.3: Belady's Optimal Page Replacement Algorithm."""

REF_STRING = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]

def simulate_optimal(refs, capacity=3):
    frames, faults = [], 0
    for i, page in enumerate(refs):
        if page not in frames:
            faults += 1
            if len(frames) == capacity:
                future = {f: (refs[i+1:].index(f) if f in refs[i+1:] else float("inf")) for f in frames}
                victim = max(future, key=future.get)
                frames.remove(victim)
            frames.append(page)
    hit_ratio = (len(refs) - faults) / len(refs) * 100
    print(f"Belady's Optimal Algorithm ({capacity} Frames):")
    print(f"Total References : {len(refs)}")
    print(f"Total Page Faults: {faults} | Hit Ratio: {hit_ratio:.2f}%")

if __name__ == "__main__":
    simulate_optimal(REF_STRING, capacity=3)
