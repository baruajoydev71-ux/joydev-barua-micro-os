#!/usr/bin/env python3
"""Experiment 19.1: Lamport Logical Clocks & Happens-Before Causal Ordering."""

class Node:
    def __init__(self, nid):
        self.nid = nid
        self.clock = 0

    def local_event(self, label):
        self.clock += 1
        print(f"  [{self.nid}] Local  '{label:<12}' -> L={self.clock}")

    def send(self, target, msg):
        self.clock += 1
        ts = self.clock
        print(f"  [{self.nid}] Send   '{msg:<12}' to {target.nid} (ts={ts})")
        target.receive(self.nid, msg, ts)

    def receive(self, src, msg, ts):
        old = self.clock
        self.clock = max(self.clock, ts) + 1
        print(f"  [{self.nid}] Recv   '{msg:<12}' from {src} (old={old}, ts={ts}) -> L={self.clock}")

if __name__ == "__main__":
    p1, p2, p3 = Node("Node-1"), Node("Node-2"), Node("Node-3")
    print("Lamport Logical Clock Execution Trace:")
    p1.local_event("init_state")
    p1.send(p2, "SYNC_REQ")
    p3.local_event("audit_tick")
    p2.send(p3, "COMMIT_MSG")
    p3.send(p1, "ACK_DONE")
    print(f"\nFinal Clocks: Node-1={p1.clock}, Node-2={p2.clock}, Node-3={p3.clock}")
