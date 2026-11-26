#!/usr/bin/env python3
"""Experiment 12.2: Double Buffering Overlap, Cache Hit Analysis & Print Spooler."""
from collections import deque

def simulate_double_buffering(blocks=5, dma_ms=6, cpu_ms=4):
    single_time = blocks * (dma_ms + cpu_ms)
    double_time = dma_ms + (blocks - 1) * max(dma_ms, cpu_ms) + cpu_ms
    speedup = single_time / double_time
    print("=== Double Buffering Throughput Analysis ===")
    print(f"  Blocks={blocks}, DMA={dma_ms}ms, CPU={cpu_ms}ms")
    print(f"  Single-Buffered Total Time : {single_time} ms")
    print(f"  Double-Buffered Total Time : {double_time} ms (Speedup: {speedup:.2f}x)\n")

def simulate_spooler():
    spool = deque([
        ("JOB-01", "joydev", "joydev_os_report.pdf", 18),
        ("JOB-02", "joydev", "lab_25BTRCL298.docx", 12),
        ("JOB-03", "joydev", "kernel_diagram.png", 4),
    ])
    print("=== Asynchronous Print Spooler Daemon ===")
    while spool:
        jid, owner, doc, pages = spool.popleft()
        print(f"  [SPOOLER] Printing {jid} | Owner={owner:<6} | File={doc:<22} | Pages={pages}")
    print("  [SPOOLER] Queue drained cleanly.")

if __name__ == "__main__":
    simulate_double_buffering()
    simulate_spooler()
