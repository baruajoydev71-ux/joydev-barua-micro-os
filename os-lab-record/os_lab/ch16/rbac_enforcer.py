#!/usr/bin/env python3
"""Experiment 16.2: Role-Based Access Control (RBAC) Policy Monitor."""

ROLE_PERMS = {
    "ADMIN":   {"read_grades", "write_grades", "deploy_kernel", "read_audit"},
    "STUDENT": {"read_grades", "submit_lab"},
    "AUDITOR": {"read_grades", "read_audit"},
    "GUEST":   {"read_public"},
}

USER_ROLES = {
    "root":    ["ADMIN"],
    "joydev":  ["STUDENT"],
    "auditor": ["AUDITOR"],
    "visitor": ["GUEST"],
}

def check_access(user, action):
    roles = USER_ROLES.get(user, [])
    allowed = any(action in ROLE_PERMS.get(r, set()) for r in roles)
    decision = "ALLOW" if allowed else "DENY "
    print(f"  [{decision}] User={user:<8} Roles={str(roles):<12} Action={action}")

if __name__ == "__main__":
    print("RBAC Least-Privilege Evaluation (Jain OS Lab):")
    requests = [
        ("joydev",  "submit_lab"),
        ("joydev",  "write_grades"),
        ("joydev",  "deploy_kernel"),
        ("root",    "deploy_kernel"),
        ("auditor", "read_audit"),
        ("visitor", "read_grades"),
    ]
    for u, act in requests:
        check_access(u, act)
