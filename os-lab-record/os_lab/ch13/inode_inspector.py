#!/usr/bin/env python3
"""Experiment 13.1: Real OS Inode Metadata Extraction via os.stat()."""
import os
import stat
import time

def inspect_directory(target="."):
    print(f"Live VFS Inode Inspection for '{os.path.abspath(target)}':\n")
    print(f"{'MODE':<11} {'LINKS':>5} {'SIZE(B)':>8} {'INODE':>20}  {'MODIFIED':<19}  NAME")
    print("-" * 82)
    for name in sorted(os.listdir(target)):
        full = os.path.join(target, name)
        st = os.stat(full)
        mode_str = stat.filemode(st.st_mode)
        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
        print(f"{mode_str:<11} {st.st_nlink:>5} {st.st_size:>8} {st.st_ino:>20}  {mtime:<19}  {name}")

if __name__ == "__main__":
    inspect_directory(".")
