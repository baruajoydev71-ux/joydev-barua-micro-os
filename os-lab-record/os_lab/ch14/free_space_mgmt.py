#!/usr/bin/env python3
"""Experiment 14.2: Disk Free-Space Management (Bitmap & Linked Free List)."""

class BitmapAllocator:
    def __init__(self, n_blocks=16):
        self.bits = [1] * n_blocks  # 1 = free, 0 = allocated

    def allocate(self, count):
        chosen = []
        for i, free in enumerate(self.bits):
            if free:
                self.bits[i] = 0
                chosen.append(i)
                if len(chosen) == count:
                    break
        return chosen

    def release(self, blocks):
        for b in blocks:
            self.bits[b] = 1

    def render(self):
        return "".join(map(str, self.bits))

if __name__ == "__main__":
    bm = BitmapAllocator(16)
    print(f"Initial Bitmap (1=Free, 0=Used) : {bm.render()}")
    f1 = bm.allocate(5)
    print(f"Allocated File A (5 blocks)     : {f1} -> Bitmap: {bm.render()}")
    f2 = bm.allocate(4)
    print(f"Allocated File B (4 blocks)     : {f2} -> Bitmap: {bm.render()}")
    bm.release([1, 2, 3])
    print(f"Released Blocks [1, 2, 3]       : Bitmap: {bm.render()}")
    free_list = [i for i, b in enumerate(bm.bits) if b == 1]
    print(f"Equivalent Linked Free List     : {' -> '.join(map(str, free_list))} -> NULL")
