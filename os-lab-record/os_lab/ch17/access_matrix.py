#!/usr/bin/env python3
"""Experiment 17.1: Lampson Access Matrix & Controlled Domain Switching."""

MATRIX = {
    "D_USER":   {"lab_code.py": {"r", "w"}, "sys_cfg": {"r"},      "D_KERNEL": {"switch"}},
    "D_KERNEL": {"lab_code.py": {"r", "w"}, "sys_cfg": {"r", "w"}, "disk0": {"r", "w"}},
    "D_GUEST":  {"lab_code.py": {"r"},      "sys_cfg": set(),      "disk0": set()},
}

def authorize(domain, obj, op):
    rights = MATRIX.get(domain, {}).get(obj, set())
    ok = op in rights
    print(f"  Check ({domain:<8}, {obj:<11}, '{op}') -> {'GRANTED' if ok else 'DENIED'}")
    return ok

if __name__ == "__main__":
    current = "D_USER"
    print(f"Active Protection Domain: {current}")
    authorize(current, "lab_code.py", "w")
    authorize(current, "sys_cfg", "w")
    if authorize(current, "D_KERNEL", "switch"):
        current = "D_KERNEL"
        print(f"  --> Domain Transitioned to {current} (Syscall Trap)")
    authorize(current, "sys_cfg", "w")
    authorize("D_GUEST", "sys_cfg", "r")
