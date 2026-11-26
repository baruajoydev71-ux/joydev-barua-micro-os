#!/usr/bin/env python3
"""Experiment 14.1: Contiguous, Linked & Indexed File Allocation Simulator."""

def demo_contiguous(total_blocks=16):
    disk = [None] * total_blocks
    for b in (2, 3, 7, 11):
        disk[b] = "USED"
    print("=== 1. Contiguous Allocation (Need 4 contiguous blocks) ===")
    start = next((i for i in range(total_blocks - 3) if all(disk[j] is None for j in range(i, i + 4))), -1)
    if start != -1:
        for j in range(start, start + 4):
            disk[j] = "joydev.bin"
        print(f"  Allocated 'joydev.bin' at contiguous range [{start}..{start + 3}]")
    else:
        print("  Allocation failed: External fragmentation!")

def demo_linked(free_blocks):
    print("\n=== 2. Linked Allocation (4 blocks across fragmented disk) ===")
    chain = free_blocks[:4]
    links = " -> ".join(str(b) for b in chain) + " -> EOF"
    print(f"  File 'logs.dat' block chain: {links}")

def demo_indexed(free_blocks):
    print("\n=== 3. Indexed Allocation (1 index block + 4 data blocks) ===")
    idx_block = free_blocks[4]
    data_blocks = free_blocks[5:9]
    print(f"  File 'kernel.img' | Index Block = #{idx_block} | Pointers = {data_blocks}")
    print(f"  O(1) Direct lookup of logical block 2 -> Physical Block #{data_blocks[2]}")

if __name__ == "__main__":
    free = [0, 1, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15]
    demo_contiguous()
    demo_linked(free)
    demo_indexed(free)
