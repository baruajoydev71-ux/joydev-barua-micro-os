#!/usr/bin/env python3
"""Experiment 18.2: Hypervisor Memory Overcommitment & Balloon Driver Simulation."""

VMS = {
    "VM-Web":   {"alloc_mb": 2048, "active_mb": 1920, "balloon_mb": 0},
    "VM-Idle":  {"alloc_mb": 2048, "active_mb":  512, "balloon_mb": 0},
    "VM-DB":    {"alloc_mb": 2048, "active_mb": 1700, "balloon_mb": 0},
}

def show_state(label):
    print(f"=== {label} ===")
    for name, m in VMS.items():
        eff = m["alloc_mb"] - m["balloon_mb"]
        print(f"  {name:<8} | Alloc={m['alloc_mb']:4d}MB | Active={m['active_mb']:4d}MB | Balloon={m['balloon_mb']:4d}MB | GuestUsable={eff:4d}MB")

if __name__ == "__main__":
    show_state("Before Host Memory Pressure")
    demand_mb = 1024
    print(f"\n[HYPERVISOR] VM-Web requests +{demand_mb} MB burst; inflating VM-Idle balloon...")
    reclaimable = VMS["VM-Idle"]["alloc_mb"] - VMS["VM-Idle"]["active_mb"] - 256
    reclaimed = min(demand_mb, reclaimable)
    VMS["VM-Idle"]["balloon_mb"] += reclaimed
    VMS["VM-Web"]["alloc_mb"] += reclaimed
    print(f"[HYPERVISOR] Reclaimed {reclaimed} MB from VM-Idle and reassigned to VM-Web.\n")
    show_state("After Dynamic Ballooning")
