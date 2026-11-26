#!/usr/bin/env python3
"""Experiment 11.2: Analytical Hard Disk Drive Access Latency Model."""

DRIVES = [
    ("Consumer 5400 RPM",  5400, 12.0, 120.0),
    ("Desktop  7200 RPM",  7200,  8.5, 180.0),
    ("Server  10000 RPM", 10000,  4.2, 240.0),
    ("Archival 15000 RPM", 15000, 2.9, 300.0),
]

def model_latency(rpm, seek_ms, rate_mb_s, payload_kb=64.0):
    t_rot = (60.0 * 1000.0) / (2.0 * rpm)
    payload_mb = payload_kb / 1024.0
    t_transfer = (payload_mb / rate_mb_s) * 1000.0
    t_total = seek_ms + t_rot + t_transfer
    iops = 1000.0 / t_total
    return t_rot, t_transfer, t_total, iops

if __name__ == "__main__":
    payload_kb = 64.0
    print(f"HDD Access Latency Comparison (Payload = {payload_kb:.0f} KB):\n")
    print(f"{'Drive Class':<20} | {'Seek(ms)':>8} | {'Rot(ms)':>7} | {'Xfer(ms)':>8} | {'Total(ms)':>9} | {'Est. IOPS':>9}")
    print("-" * 76)
    for name, rpm, seek, rate in DRIVES:
        rot, xfer, tot, iops = model_latency(rpm, seek, rate, payload_kb)
        print(f"{name:<20} | {seek:>8.2f} | {rot:>7.2f} | {xfer:>8.3f} | {tot:>9.3f} | {iops:>9.1f}")
