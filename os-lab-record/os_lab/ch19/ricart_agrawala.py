#!/usr/bin/env python3
"""Experiment 19.2: Ricart-Agrawala Distributed Mutual Exclusion Simulator."""

def simulate_ricart_agrawala(n_nodes=4, contenders=((2, 10), (1, 10), (3, 14))):
    print(f"Cluster Size N={n_nodes} | Simultaneous CS Requests (Node, Lamport_TS): {list(contenders)}\n")
    ordered = sorted(contenders, key=lambda x: (x[1], x[0]))  # Tie-break by (ts, node_id)
    msgs = 0
    for node_id, ts in ordered:
        peers = [p for p in range(1, n_nodes + 1) if p != node_id]
        msgs += 2 * len(peers)
        print(f"  [Node-{node_id} | ts={ts}] Broadcast REQUEST to {peers}")
        print(f"  [Node-{node_id} | ts={ts}] Received {len(peers)}/{len(peers)} REPLY grants -> ENTER CRITICAL SECTION")
        print(f"  [Node-{node_id} | ts={ts}] EXIT CS -> Flushing deferred REPLY queue\n")
    print(f"Total Control Messages Exchanged: {msgs} (= {len(ordered)} x 2*(N-1))")

if __name__ == "__main__":
    simulate_ricart_agrawala()
