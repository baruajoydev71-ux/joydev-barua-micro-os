#!/usr/bin/env python3
"""Experiment 16.1: Salted PBKDF2-HMAC-SHA256 Authentication Engine."""
import hashlib
import hmac
import os

SHADOW_DB = {}
ITERATIONS = 100_000

def register_user(username, password):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    SHADOW_DB[username] = (salt, dk)
    print(f"[REGISTER] User='{username}' | Salt={salt.hex()[:16]}... | Hash={dk.hex()[:24]}...")

def authenticate(username, candidate):
    if username not in SHADOW_DB:
        return False
    salt, expected_dk = SHADOW_DB[username]
    test_dk = hashlib.pbkdf2_hmac("sha256", candidate.encode(), salt, ITERATIONS)
    return hmac.compare_digest(expected_dk, test_dk)

if __name__ == "__main__":
    register_user("joydev", "OSLab@25BTRCL298")
    register_user("lab_clone", "OSLab@25BTRCL298")  # Same password, unique salt!
    print("\nAuthentication Verification Tests:")
    for user, pw in [("joydev", "OSLab@25BTRCL298"), ("joydev", "WrongPass!"), ("guest", "1234")]:
        ok = authenticate(user, pw)
        print(f"  Login user='{user:<8}' pw='{pw:<16}' -> {'ACCESS GRANTED' if ok else 'ACCESS DENIED'}")
