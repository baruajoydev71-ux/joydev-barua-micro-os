#!/usr/bin/env python3
"""Experiment 9.3: Paged Logical-to-Physical Address Translation."""

PAGE_SIZE = 1024  # 1 KiB pages (10-bit offset)
PAGE_TABLE = {0: 5, 1: 2, 2: 8, 3: 1, 4: 12}

def translate(logical_addr):
    page = logical_addr // PAGE_SIZE
    offset = logical_addr % PAGE_SIZE
    if page not in PAGE_TABLE:
        return None, f"PAGE FAULT (Page {page} not resident in RAM)"
    frame = PAGE_TABLE[page]
    phys = frame * PAGE_SIZE + offset
    return phys, f"Page {page} -> Frame {frame:2d}, Offset {offset:4d}"

if __name__ == "__main__":
    print(f"Paged Address Translation (Page Size = {PAGE_SIZE} B):")
    for addr in [1500, 3120, 4200, 8500]:
        phys, detail = translate(addr)
        print(f"  Logical {addr:5d} -> Physical: {str(phys):>5}  [{detail}]")
