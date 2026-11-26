#!/usr/bin/env python3
"""Experiment 10.2: Least Recently Used (LRU) Page Replacement."""

REF_STRING = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]

def simulate_lru(refs, capacity=3):
    frames, last_seen, faults = [], {}, 0
    for step, page in enumerate(refs):
        if page not in frames:
            faults += 1
            if len(frames) == capacity:
                victim = min(frames, key=lambda p: last_seen[p])
                frames.remove(victim)
            frames.append(page)
        last_seen[page] = step
    hit_ratio = (len(refs) - faults) / len(refs) * 100
    print(f"LRU Page Replacement ({capacity} Frames):")
    print(f"Total References : {len(refs)}")
    print(f"Total Page Faults: {faults} | Hit Ratio: {hit_ratio:.2f}%")

if __name__ == "__main__":
    simulate_lru(REF_STRING, capacity=3)
