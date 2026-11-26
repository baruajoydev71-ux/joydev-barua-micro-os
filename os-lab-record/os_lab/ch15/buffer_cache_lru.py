#!/usr/bin/env python3
"""Experiment 15.1: Unified Buffer Cache with LRU Eviction & Dirty Write-Back."""
from collections import OrderedDict

class UnifiedBufferCache:
    def __init__(self, capacity=3):
        self.cap = capacity
        self.cache = OrderedDict()  # block_id -> dirty(bool)
        self.hits = 0
        self.misses = 0
        self.flushes = 0

    def access(self, block_id, write=False):
        op = "WRITE" if write else "READ "
        if block_id in self.cache:
            self.hits += 1
            self.cache.move_to_end(block_id)
            if write:
                self.cache[block_id] = True
            print(f"  {op} Block {block_id:2d} -> CACHE HIT   | Cache={list(self.cache.items())}")
            return
        self.misses += 1
        evicted = ""
        if len(self.cache) >= self.cap:
            v_blk, v_dirty = self.cache.popitem(last=False)
            if v_dirty:
                self.flushes += 1
                evicted = f" [Evict #{v_blk} -> FLUSH DIRTY]"
            else:
                evicted = f" [Evict #{v_blk} (Clean)]"
        self.cache[block_id] = write
        print(f"  {op} Block {block_id:2d} -> CACHE MISS {evicted} | Cache={list(self.cache.items())}")

if __name__ == "__main__":
    bc = UnifiedBufferCache(capacity=3)
    workload = [(10, False), (11, True), (12, False), (10, False), (13, True), (11, False), (14, False)]
    print("Unified Buffer Cache Trace (Capacity = 3 Blocks):")
    for blk, is_wr in workload:
        bc.access(blk, write=is_wr)
    total = bc.hits + bc.misses
    print(f"\nSummary: Hits={bc.hits}, Misses={bc.misses} (Hit Ratio={bc.hits/total*100:.1f}%), Dirty Flushes={bc.flushes}")
