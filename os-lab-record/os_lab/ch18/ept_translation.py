#!/usr/bin/env python3
"""Experiment 18.1: Hypervisor Two-Level Translation (GVA -> GPA -> HPA)."""

PAGE_SIZE = 4096
GUEST_PT = {0: 4, 1: 7, 2: 12}      # Guest VPN -> Guest PFN
EPT      = {4: 102, 7: 255, 12: 310} # Guest PFN -> Host PFN

def translate_gva(gva):
    g_vpn, offset = divmod(gva, PAGE_SIZE)
    if g_vpn not in GUEST_PT:
        return f"GVA 0x{gva:04X} -> GUEST PAGE FAULT (VPN {g_vpn} unmapped)"
    g_pfn = GUEST_PT[g_vpn]
    gpa = g_pfn * PAGE_SIZE + offset
    if g_pfn not in EPT:
        return f"GVA 0x{gva:04X} -> GPA 0x{gpa:05X} -> EPT VIOLATION (VM-Exit)"
    h_pfn = EPT[g_pfn]
    hpa = h_pfn * PAGE_SIZE + offset
    return (
        f"GVA 0x{gva:04X} (VPN={g_vpn}, Off=0x{offset:03X}) -> "
        f"GPA 0x{gpa:05X} (GPFN={g_pfn}) -> HPA 0x{hpa:06X} (HPFN={h_pfn})"
    )

if __name__ == "__main__":
    print("Two-Level EPT Address Translation (4 KB Pages):")
    for addr in [0x0124, 0x10A8, 0x2F00, 0x4010]:
        print(" ", translate_gva(addr))
