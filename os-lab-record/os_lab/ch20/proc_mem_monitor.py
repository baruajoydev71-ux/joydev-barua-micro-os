#!/usr/bin/env python3
"""Experiment 20.1: Live Process Memory Footprint & Status Inspector."""
import ctypes
import os
import platform

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]

def inspect_process_memory():
    print(f"Host Kernel   : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Process PID   : {os.getpid()} | PPID: {os.getppid()}")
    if os.path.exists("/proc/self/status"):
        with open("/proc/self/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith(("Name:", "State:", "VmSize:", "VmRSS:", "Threads:")):
                    print(" ", line.strip())
    else:
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        hproc = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.psapi.GetProcessMemoryInfo(hproc, ctypes.byref(pmc), pmc.cb)
        print(f"VmRSS (WorkingSet) : {pmc.WorkingSetSize / 1024:,.1f} KB")
        print(f"Peak Working Set   : {pmc.PeakWorkingSetSize / 1024:,.1f} KB")
        print(f"Committed Pagefile : {pmc.PagefileUsage / 1024:,.1f} KB")
        print(f"Hard/Soft Faults   : {pmc.PageFaultCount:,}")

if __name__ == "__main__":
    inspect_process_memory()
