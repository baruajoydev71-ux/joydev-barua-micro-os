#!/usr/bin/env python3
"""Experiment 3.2: Bitmap-Based OS PID Allocator [300..5000]."""

MIN_PID = 300
MAX_PID = 5000
NUM_PIDS = MAX_PID - MIN_PID + 1

class PidManager:
    def __init__(self):
        self.bitmap = bytearray(NUM_PIDS)

    def allocate_pid(self):
        for idx in range(NUM_PIDS):
            if self.bitmap[idx] == 0:
                self.bitmap[idx] = 1
                return MIN_PID + idx
        return -1

    def release_pid(self, pid):
        if MIN_PID <= pid <= MAX_PID:
            self.bitmap[pid - MIN_PID] = 0

if __name__ == "__main__":
    mgr = PidManager()
    pids = [mgr.allocate_pid() for _ in range(4)]
    print("Allocated initial PIDs:", pids)
    print(f"Releasing PID {pids[1]} back to free pool...")
    mgr.release_pid(pids[1])
    reused = mgr.allocate_pid()
    print(f"Next allocated PID (reclaimed): {reused}")
