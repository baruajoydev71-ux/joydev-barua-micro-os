#!/usr/bin/env python3
"""Experiment 6.1: Mutex-Protected Finite Resource Pool (Ex 6.33)."""
import threading

MAX_RESOURCES = 5
available_resources = MAX_RESOURCES
pool_lock = threading.Lock()

def decrease_count(count, caller):
    global available_resources
    with pool_lock:
        if available_resources < count:
            print(f"[{caller}] DENIED request for {count} units (Available: {available_resources})")
            return -1
        available_resources -= count
        print(f"[{caller}] ACQUIRED {count} units (Remaining: {available_resources})")
        return 0

def increase_count(count, caller):
    global available_resources
    with pool_lock:
        available_resources += count
        print(f"[{caller}] RELEASED {count} units (Remaining: {available_resources})")

if __name__ == "__main__":
    print(f"Initial resource pool capacity: {available_resources}")
    decrease_count(3, "Worker-A")
    decrease_count(2, "Worker-B")
    status = decrease_count(1, "Worker-C")
    print(f"Over-allocation return code: {status}")
    increase_count(3, "Worker-A")
    decrease_count(2, "Worker-C")
