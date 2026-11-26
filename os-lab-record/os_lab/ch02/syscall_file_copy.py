#!/usr/bin/env python3
"""Experiment 2.1: Unbuffered Low-Level File Copy via OS File Descriptors."""
import os
import sys

BUFFER_SIZE = 4096

def syscall_copy(src_path, dst_path):
    src_fd = os.open(src_path, os.O_RDONLY)
    dst_flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    dst_fd = os.open(dst_path, dst_flags, 0o644)
    print(f"Allocated File Descriptors: src_fd={src_fd}, dst_fd={dst_fd}")

    total_bytes = 0
    try:
        while True:
            chunk = os.read(src_fd, BUFFER_SIZE)
            if not chunk:
                break
            written = os.write(dst_fd, chunk)
            if written != len(chunk):
                raise IOError("Partial write detected on destination descriptor")
            total_bytes += written
    finally:
        os.close(src_fd)
        os.close(dst_fd)

    print(f"Transfer complete: {src_path} -> {dst_path} ({total_bytes} bytes)")
    with open(dst_path, "r", encoding="utf-8") as verify:
        print("Verified payload:", verify.read().strip())

if __name__ == "__main__":
    syscall_copy(sys.argv[1], sys.argv[2])
