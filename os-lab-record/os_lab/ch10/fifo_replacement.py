#!/usr/bin/env python3
"""Experiment 10.1: FIFO Page Replacement Simulation."""

REF_STRING = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]

def simulate_fifo(refs, capacity=3):
    frames, faults = [], 0
    print(f"FIFO Page Replacement ({capacity} Frames):")
    for idx, page in enumerate(refs):
        if page not in frames:
            faults += 1
            if len(frames) == capacity:
                frames.pop(0)
            frames.append(page)
            tag = "FAULT"
        else:
            tag = "HIT  "
        if idx < 10:
            print(f"  Step {idx+1:2d} | Ref {page} | Frames={str(frames):<12} | {tag}")
    hit_ratio = (len(refs) - faults) / len(refs) * 100
    print(f"  ... (20 total references)")
    print(f"Total Page Faults: {faults} | Hit Ratio: {hit_ratio:.2f}%")

if __name__ == "__main__":
    simulate_fifo(REF_STRING, capacity=3)
