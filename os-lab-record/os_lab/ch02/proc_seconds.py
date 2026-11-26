#!/usr/bin/env python3
"""Experiment 2.2: Virtual /proc/seconds Monotonic Uptime Interface."""
import time

class VirtualProcSeconds:
    def __init__(self):
        self.load_time = time.monotonic()
        print("[/proc/seconds] Kernel module registered. Initial monotonic clock latched.")

    def read_entry(self):
        elapsed = time.monotonic() - self.load_time
        return f"{elapsed:.2f} seconds"

    def unload(self):
        print("[/proc/seconds] Virtual entry removed and module unloaded cleanly.")

if __name__ == "__main__":
    vproc = VirtualProcSeconds()
    for sample in range(5):
        print(f"  read(/proc/seconds) [sample {sample}] -> {vproc.read_entry()}")
        if sample < 4:
            time.sleep(0.25)
    vproc.unload()
