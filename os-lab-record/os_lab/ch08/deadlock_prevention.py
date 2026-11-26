#!/usr/bin/env python3
"""Experiment 8.3: Deadlock Prevention via Global Resource Hierarchy."""

RANK = {"Disk": 1, "Printer": 2, "MemoryBus": 3, "NetworkNIC": 4}

def request_resource(held, requested):
    max_held = max((RANK[r] for r in held), default=0)
    req_rank = RANK[requested]
    if req_rank > max_held:
        held.append(requested)
        return f"GRANTED : {requested:<10} (Rank {req_rank}) > Max Held ({max_held})"
    return f"DENIED  : {requested:<10} (Rank {req_rank}) <= Max Held ({max_held}) [Order Violation]"

if __name__ == "__main__":
    held_resources = ["Disk"]
    print("Initial Held Resources:", held_resources)
    print(request_resource(held_resources, "Printer"))
    print(request_resource(held_resources, "MemoryBus"))
    print(request_resource(held_resources, "Disk"))
    print(request_resource(held_resources, "NetworkNIC"))
