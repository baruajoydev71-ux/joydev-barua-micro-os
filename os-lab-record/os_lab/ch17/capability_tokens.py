#!/usr/bin/env python3
"""Experiment 17.2: Cryptographically Sealed Capability Token Engine."""
import hashlib
import hmac

KERNEL_SECRET = b"joydev_microkernel_cap_key_25BTRCL298"

def mint_capability(subject, obj, rights):
    payload = f"{subject}|{obj}|{','.join(sorted(rights))}"
    sig = hmac.new(KERNEL_SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16]
    return {"subject": subject, "object": obj, "rights": sorted(rights), "mac": sig}

def verify_capability(cap, requested_right):
    payload = f"{cap['subject']}|{cap['object']}|{','.join(sorted(cap['rights']))}"
    expected = hmac.new(KERNEL_SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(cap["mac"], expected):
        return "REJECTED (Forged/Tampered MAC!)"
    if requested_right not in cap["rights"]:
        return f"DENIED (Right '{requested_right}' absent)"
    return "AUTHORIZED"

if __name__ == "__main__":
    cap = mint_capability("joydev", "/dev/tty0", ["read"])
    print(f"Minted Capability : {cap}")
    print(f"  Verify 'read'   : {verify_capability(cap, 'read')}")
    print(f"  Verify 'write'  : {verify_capability(cap, 'write')}")
    forged = dict(cap, rights=["read", "write"])
    print(f"  Verify Forged   : {verify_capability(forged, 'write')}")
