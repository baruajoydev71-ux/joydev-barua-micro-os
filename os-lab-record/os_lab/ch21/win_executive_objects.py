#!/usr/bin/env python3
"""Experiment 21.1: Windows NT Executive Process/Thread Objects & Live Win32 API."""
import ctypes
import os
import platform

class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]

def ft_to_ms(ft):
    ticks = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return ticks / 10_000.0  # 100-ns units -> milliseconds

if __name__ == "__main__":
    k32 = ctypes.windll.kernel32
    pid = k32.GetCurrentProcessId()
    tid = k32.GetCurrentThreadId()
    hproc = k32.GetCurrentProcess()
    _ = sum(i * i for i in range(450_000))  # Measurable user-mode burst
    for _ in range(400):
        os.stat(__file__)                    # Measurable kernel-mode syscalls
    c_ft, e_ft, k_ft, u_ft = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    k32.GetProcessTimes(
        hproc, ctypes.byref(c_ft), ctypes.byref(e_ft), ctypes.byref(k_ft), ctypes.byref(u_ft)
    )

    handles = [
        ("0x004", "File(os_lab.log)"),
        ("0x008", "Mutex(SyncLock)"),
        ("0x00C", "Section(SharedMem)"),
    ]
    print(f"Windows Platform : {platform.platform()}")
    print("=== Live Win32 Executive Telemetry ===")
    print(f"  Active PID / TID   : {pid} / {tid}")
    print(f"  Kernel Mode Time   : {ft_to_ms(k_ft):.3f} ms")
    print(f"  User Mode Time     : {ft_to_ms(u_ft):.3f} ms")
    print("\n=== Modeled EPROCESS Object Descriptor ===")
    print(f"  ImageName          : joydev_app.exe")
    print(f"  UniqueProcessId    : {pid}  |  PrimaryThreadId : {tid}")
    print(f"  PriorityClass      : NORMAL_PRIORITY_CLASS (Base 8)")
    print("  HandleTable        :")
    for h_id, obj in handles:
        print(f"      [{h_id}] -> {obj}")
