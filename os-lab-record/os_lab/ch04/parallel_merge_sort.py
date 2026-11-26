#!/usr/bin/env python3
"""Experiment 4.4: Multithreaded Parallel Divide-and-Conquer Merge Sort."""
import threading

def sort_half(sublist, out_slots, slot_idx):
    out_slots[slot_idx] = sorted(sublist)

def merge_sorted(left, right):
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

if __name__ == "__main__":
    arr = [64, 19, 88, 5, 41, 73, 12, 97, 28, 53]
    mid = len(arr) // 2
    halves = [None, None]
    t1 = threading.Thread(target=sort_half, args=(arr[:mid], halves, 0))
    t2 = threading.Thread(target=sort_half, args=(arr[mid:], halves, 1))
    t1.start(); t2.start()
    t1.join(); t2.join()

    result = merge_sorted(halves[0], halves[1])
    print("Unsorted Input :", arr)
    print("Left Sorted    :", halves[0])
    print("Right Sorted   :", halves[1])
    print("Merged Output  :", result)
