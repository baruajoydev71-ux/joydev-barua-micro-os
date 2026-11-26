#!/usr/bin/env python3
"""Experiment 12.1: Kernel Device Driver I/O Request Queue Scheduler."""
import heapq

REQUESTS = [
    # (priority: lower=higher, req_id, device, service_ms, desc)
    (3, "IO-101", "NVMe0", 14, "Background log flush"),
    (1, "IO-102", "NVMe0",  3, "Demand page-in (PID 412)"),
    (2, "IO-103", "NVMe0",  6, "Interactive file read"),
    (1, "IO-104", "NVMe0",  2, "Swap-in critical metadata"),
    (3, "IO-105", "NVMe0", 12, "Checkpoint backup write"),
]

def dispatch(order, label):
    t, total_wait = 0, 0
    print(f"=== {label} ===")
    for prio, rid, dev, svc, desc in order:
        wait = t
        total_wait += wait
        t += svc
        print(f"  {rid} [P{prio}] ({dev}) | Wait={wait:2d}ms | Svc={svc:2d}ms | Done={t:2d}ms | {desc}")
    print(f"  -> Average Wait Time: {total_wait / len(order):.2f} ms\n")

if __name__ == "__main__":
    dispatch(REQUESTS, "FIFO Device Queue")
    pq = list(REQUESTS)
    heapq.heapify(pq)
    prio_order = [heapq.heappop(pq) for _ in range(len(pq))]
    dispatch(prio_order, "Priority-Ordered Device Driver Queue")
