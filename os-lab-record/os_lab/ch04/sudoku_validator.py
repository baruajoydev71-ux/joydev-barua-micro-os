#!/usr/bin/env python3
"""Experiment 4.3: 27-Thread Concurrent 9x9 Sudoku Validator."""
import threading

GRID = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]
VALID = [False] * 27
TARGET = set(range(1, 10))

def check_row(r, idx):
    VALID[idx] = (set(GRID[r]) == TARGET)

def check_col(c, idx):
    VALID[idx] = ({GRID[r][c] for r in range(9)} == TARGET)

def check_box(sr, sc, idx):
    VALID[idx] = ({GRID[r][c] for r in range(sr, sr + 3) for c in range(sc, sc + 3)} == TARGET)

if __name__ == "__main__":
    threads = []
    for i in range(9):
        threads.append(threading.Thread(target=check_row, args=(i, i)))
        threads.append(threading.Thread(target=check_col, args=(i, 9 + i)))
    for r in range(0, 9, 3):
        for c in range(0, 9, 3):
            box_idx = 18 + (r // 3) * 3 + (c // 3)
            threads.append(threading.Thread(target=check_box, args=(r, c, box_idx)))

    for t in threads: t.start()
    for t in threads: t.join()

    print(f"Total validator threads executed : {len(threads)}")
    print(f"All 27 constraints satisfied     : {all(VALID)}")
    print("Sudoku Verification Status       :", "VALID SOLUTION" if all(VALID) else "INVALID")
