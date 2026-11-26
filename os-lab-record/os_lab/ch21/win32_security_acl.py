#!/usr/bin/env python3
"""Experiment 21.2: Windows Security Reference Monitor (DACL/SACL Evaluation)."""

SECURITY_DESCRIPTOR = {
    "Object": r"C:\Users\joydev\os_lab\exam_grades.dat",
    "OwnerSID": "SID_JOYDEV_25BTRCL298",
    "DACL": [
        ("DENY",  "SID_GUEST",              {"READ", "WRITE", "DELETE"}),
        ("ALLOW", "SID_JOYDEV_25BTRCL298",  {"READ", "WRITE"}),
        ("ALLOW", "SID_SYSTEM",             {"READ", "WRITE", "DELETE"}),
    ],
    "SACL": [
        ("AUDIT_FAILURE", "WRITE"),
        ("AUDIT_SUCCESS", "DELETE"),
    ],
}

def access_check(sid, desired_right):
    decision = "DENIED (Implicit Default)"
    for ace_type, ace_sid, rights in SECURITY_DESCRIPTOR["DACL"]:
        if ace_sid == sid and desired_right in rights:
            decision = "DENIED (Explicit DENY ACE)" if ace_type == "DENY" else "GRANTED (ALLOW ACE)"
            break
    audit = []
    for event_type, right in SECURITY_DESCRIPTOR["SACL"]:
        if right == desired_right:
            if event_type == "AUDIT_FAILURE" and decision.startswith("DENIED"):
                audit.append("SACL:LoggedFailedWrite")
            if event_type == "AUDIT_SUCCESS" and decision.startswith("GRANTED"):
                audit.append("SACL:LoggedDelete")
    tag = f" | {', '.join(audit)}" if audit else ""
    print(f"  SID={sid:<22} Right={desired_right:<6} -> {decision}{tag}")

if __name__ == "__main__":
    print(f"Securable Object : {SECURITY_DESCRIPTOR['Object']}")
    print(f"Owner SID        : {SECURITY_DESCRIPTOR['OwnerSID']}\n")
    for sid, right in [
        ("SID_JOYDEV_25BTRCL298", "READ"),
        ("SID_JOYDEV_25BTRCL298", "WRITE"),
        ("SID_JOYDEV_25BTRCL298", "DELETE"),
        ("SID_GUEST",             "WRITE"),
        ("SID_SYSTEM",            "DELETE"),
    ]:
        access_check(sid, right)
