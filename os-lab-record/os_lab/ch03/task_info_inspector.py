#!/usr/bin/env python3
"""Experiment 3.7: Live Process & Kernel Task Descriptor Inspector."""
import os
import platform
import threading

def inspect_current_task():
    pid = os.getpid()
    ppid = os.getppid()
    print(f"=== Kernel Task Information for PID {pid} ===")
    print(f"  Process Name : {os.path.basename(__file__)}")
    print(f"  State        : R (RUNNING)")
    print(f"  PID / PPID   : {pid} / {ppid}")
    print(f"  Active Thrds : {threading.active_count()}")
    print(f"  CPU Cores    : {os.cpu_count()}")
    print(f"  OS Kernel    : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"  Owner        : Joydev Barua (25BTRCL298)")

if __name__ == "__main__":
    inspect_current_task()
