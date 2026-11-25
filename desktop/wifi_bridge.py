#!/usr/bin/env python3
"""
Joydev Micro-OS Desktop - Live Host Wi-Fi Bridge Server
Developed by Joydev Barua

Reads live Windows Wi-Fi interface, IP configuration, and nearby wireless
networks using native OS tools (netsh, ipconfig, ping) and exposes them on
http://127.0.0.1:8765 so Joydev Micro-OS Desktop always shows the exact Wi-Fi
network connected to the host device.
"""

import ctypes
import http.server
import ipaddress
import json
import os
import re
import socket
import socketserver
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8765
DESKTOP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DESKTOP_DIR)
INDEX_HTML_PATH = os.path.join(DESKTOP_DIR, "index.html")

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_LAST_SCAN_TIME = 0.0
_SCAN_LOCK = threading.Lock()

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
CWD_SENTINEL = "__JOYDEV_DEVTERM_CWD__="
EXIT_SENTINEL = "__JOYDEV_DEVTERM_EXIT__="

_TERM_LOCK = threading.Lock()
_TERM_SESSIONS: Dict[str, Dict[str, Any]] = {}


def build_dev_env() -> Dict[str, str]:
    env = os.environ.copy()
    user_profile = env.get("USERPROFILE") or os.path.expanduser("~")
    local_app_data = env.get("LOCALAPPDATA") or os.path.join(user_profile, "AppData", "Local")

    extra_paths = [
        os.path.join(user_profile, ".cargo", "bin"),
        os.path.join(local_app_data, "Python", "bin"),
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Git\usr\bin",
    ]
    existing_path = env.get("PATH", "")
    prepend = [p for p in extra_paths if os.path.isdir(p) and p.lower() not in existing_path.lower()]
    if prepend:
        env["PATH"] = ";".join(prepend) + ";" + existing_path

    # Use installed GNU toolchain automatically so cargo run/test link cleanly without MSVC link.exe
    gnu_toolchain_dir = os.path.join(user_profile, ".rustup", "toolchains", "stable-x86_64-pc-windows-gnu")
    if os.path.isdir(gnu_toolchain_dir) and "RUSTUP_TOOLCHAIN" not in env:
        env["RUSTUP_TOOLCHAIN"] = "stable-x86_64-pc-windows-gnu"

    env["PYTHONIOENCODING"] = "utf-8"
    env["CARGO_TERM_COLOR"] = "never"
    env["NO_COLOR"] = "1"
    return env


def get_term_session(session_id: str) -> Dict[str, Any]:
    sid = (session_id or "default").strip() or "default"
    with _TERM_LOCK:
        if sid not in _TERM_SESSIONS:
            start_cwd = PROJECT_ROOT if os.path.isdir(PROJECT_ROOT) else os.path.expanduser("~")
            _TERM_SESSIONS[sid] = {
                "cwd": start_cwd,
                "prev_cwd": start_cwd,
                "proc": None,
            }
        return _TERM_SESSIONS[sid]


def kill_proc_tree(pid: int) -> None:
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            timeout=5,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception:
        pass


def normalize_unix_shorthands(cmd: str) -> str:
    stripped = cmd.strip()
    # Map common Linux ls flags smoothly to PowerShell Get-ChildItem
    if re.match(r"^ls(\s+-[lahtrA]+)+(\s+.*)?$", stripped):
        rest = re.sub(r"^ls(\s+-[lahtrA]+)+", "", stripped).strip()
        return f"Get-ChildItem -Force {rest}".strip()
    if stripped in ("ll", "la"):
        return "Get-ChildItem -Force"
    if stripped.lower() == "ifconfig":
        return "ipconfig"
    if re.match(r"^touch\s+(.+)$", stripped):
        target = stripped[5:].strip()
        return f"New-Item -ItemType File -Force -Path {target} | Out-Null"
    if re.match(r"^head\s+-n\s+(\d+)\s+(.+)$", stripped):
        m = re.match(r"^head\s+-n\s+(\d+)\s+(.+)$", stripped)
        if m:
            return f"Get-Content -TotalCount {m.group(1)} {m.group(2)}"
    if re.match(r"^tail\s+-n\s+(\d+)\s+(.+)$", stripped):
        m = re.match(r"^tail\s+-n\s+(\d+)\s+(.+)$", stripped)
        if m:
            return f"Get-Content -Tail {m.group(1)} {m.group(2)}"
    return stripped


def clean_powershell_stderr(raw_err: str, original_cmd: str) -> str:
    """Remove internal PowerShell wrapper noise from stderr so user errors stay clean."""
    if not raw_err:
        return ""
    text = ANSI_RE.sub("", raw_err).strip()
    if not text:
        return ""

    # Clean up CommandNotFoundException neatly
    m_not_found = re.search(r"The term '([^']+)' is not recognized as the name of a cmdlet", text)
    if m_not_found:
        bad_cmd = m_not_found.group(1)
        return f"devterm: '{bad_cmd}' is not recognized as a command or program. Type 'help' to see available commands.\n"

    # Strip internal wrapper lines if present
    cleaned_lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("At line:1 char:"):
            continue
        if "$ErrorActionPreference" in line or "$global:LASTEXITCODE" in line or CWD_SENTINEL in line or EXIT_SENTINEL in line:
            continue
        if s.startswith("+ ~") or s.startswith("+ CategoryInfo") or s.startswith("+ FullyQualifiedErrorId"):
            continue
        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    return (result + "\n") if result else (text + "\n")


def execute_terminal_command(command: str, session_id: str = "default") -> Dict[str, Any]:
    sess = get_term_session(session_id)
    cmd = (command or "").strip()
    t0 = time.time()

    if not cmd:
        return {"ok": True, "stdout": "", "stderr": "", "exit_code": 0, "cwd": sess["cwd"], "duration_ms": 0}

    cmd_norm = re.sub(r"\s+", " ", cmd.lower()).strip()

    # Built-in identity & Joydev Micro-OS commands
    if cmd_norm in ("whoami", "who am i", "who ami", "who"):
        return {
            "ok": True,
            "stdout": "Joydev Barua\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    if cmd_norm in ("user", "users"):
        return {
            "ok": True,
            "stdout": "User: Joydev Barua (joydev@joydev-micro-os)\nRole: Operating Systems CA-6 Developer\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    if cmd_norm == "id":
        return {
            "ok": True,
            "stdout": 'uid=1000(joydev) gid=1000(micro-os) groups=1000(micro-os),27(sudo),100(kernel-dev) name="Joydev Barua"\n',
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    if cmd_norm == "hostname":
        return {
            "ok": True,
            "stdout": "joydev-micro-os\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    if cmd_norm in ("uname", "uname -a", "uname -s", "uname -r"):
        return {
            "ok": True,
            "stdout": "Joydev Micro-OS 0.1.0-ca6 x86_64 Rust-Microkernel (Owner: Joydev Barua)\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    if cmd_norm in ("date", "time"):
        now_str = time.strftime("%a %b %d %H:%M:%S %Y")
        return {
            "ok": True,
            "stdout": now_str + "\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    if cmd_norm in ("neofetch", "sysinfo", "about"):
        snap = collect_wifi_snapshot()
        iface = snap.get("interface", {})
        net_cfg = snap.get("network_config", {})
        wifi_str = f"{iface.get('ssid')} ({iface.get('signal_pct')}% • {net_cfg.get('cidr')})" if iface.get("connected") else "Disconnected"
        info = (
            "   _____               _                __  __ _                 ___  ____  \n"
            "  |_   _|__  _   _  __| | _____   __   |  \\/  (_) ___ _ __ ___  / _ \\/ ___| \n"
            "    | |/ _ \\| | | |/ _` |/ _ \\ \\ / /   | |\\/| | |/ __| '__/ _ \\| | | \\___ \\ \n"
            "  __| | (_) | |_| | (_| |  __/\\ V /    | |  | | | (__| | | (_) | |_| |___) |\n"
            " |___/ \\___/ \\__, |\\__,_|\\___| \\_/     |_|  |_|_|\\___|_|  \\___/ \\___/|____/ \n"
            "             |___/                                                          \n"
            f"  User      : Joydev Barua (joydev@joydev-micro-os)\n"
            f"  OS        : Joydev Micro-OS Desktop [CA-6 Metro Ash Edition]\n"
            f"  Kernel    : Rust Microkernel v0.1.0-ca6 (x86_64)\n"
            f"  Scheduler : Round Robin + MLFQ Specialization\n"
            f"  Wi-Fi     : {wifi_str}\n"
            f"  Adapter   : {iface.get('driver', 'Intel Wi-Fi')}\n"
            f"  Workdir   : {sess['cwd']}\n"
        )
        return {
            "ok": True,
            "stdout": info,
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    # Built-in reset
    if cmd_norm == "reset":
        new_cwd = PROJECT_ROOT if os.path.isdir(PROJECT_ROOT) else os.path.expanduser("~")
        sess["prev_cwd"] = sess["cwd"]
        sess["cwd"] = new_cwd
        return {
            "ok": True,
            "stdout": f"Session reset. Working directory: {new_cwd}\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": new_cwd,
            "duration_ms": 0,
        }

    # Built-in pwd
    if cmd_norm == "pwd":
        return {
            "ok": True,
            "stdout": sess["cwd"] + "\n",
            "stderr": "",
            "exit_code": 0,
            "cwd": sess["cwd"],
            "duration_ms": 0,
        }

    # Built-in pure cd (single command without chaining)
    cd_match = re.match(r"^cd(?:\s+(.+))?$", cmd, flags=re.IGNORECASE)
    if cd_match and not any(tok in cmd for tok in (";", "&&", "||", "|")):
        raw_target = (cd_match.group(1) or "").strip()
        if len(raw_target) >= 2 and raw_target[0] == raw_target[-1] and raw_target[0] in ("'", '"'):
            raw_target = raw_target[1:-1]

        if not raw_target or raw_target == "~":
            target = os.path.expanduser("~")
        elif raw_target == "-":
            target = sess.get("prev_cwd", sess["cwd"])
        elif raw_target.startswith("~/") or raw_target.startswith("~\\"):
            target = os.path.join(os.path.expanduser("~"), raw_target[2:])
        else:
            target = raw_target if os.path.isabs(raw_target) else os.path.join(sess["cwd"], raw_target)

        target = os.path.normpath(target)
        if os.path.isdir(target):
            sess["prev_cwd"] = sess["cwd"]
            sess["cwd"] = target
            return {
                "ok": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "cwd": target,
                "duration_ms": int((time.time() - t0) * 1000),
            }
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"cd: cannot find directory '{raw_target}'\n",
            "exit_code": 1,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }

    ps_cmd = normalize_unix_shorthands(cmd)
    # Wrap PowerShell command so we also capture final working directory and exit status
    wrapped = (
        "$ErrorActionPreference = 'Continue'; "
        "$global:LASTEXITCODE = 0; "
        f"{ps_cmd}\n"
        "$__ok = $?; "
        "$__ec = if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $LASTEXITCODE } elseif (-not $__ok) { 1 } else { 0 }; "
        f"Write-Output ('{CWD_SENTINEL}' + (Get-Location).Path); "
        f"Write-Output ('{EXIT_SENTINEL}' + $__ec)"
    )

    env = build_dev_env()
    try:
        proc = subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                wrapped,
            ],
            cwd=sess["cwd"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )
        sess["proc"] = proc

        try:
            raw_out, raw_err = proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            kill_proc_tree(proc.pid)
            try:
                raw_out, raw_err = proc.communicate(timeout=3)
            except Exception:
                raw_out, raw_err = "", ""
            raw_err = (raw_err or "") + "\n[TIMEOUT] Command exceeded 60s limit and was terminated.\n"
            return {
                "ok": False,
                "stdout": ANSI_RE.sub("", raw_out or "")[:200000],
                "stderr": ANSI_RE.sub("", raw_err)[:50000],
                "exit_code": 124,
                "cwd": sess["cwd"],
                "duration_ms": int((time.time() - t0) * 1000),
            }
        finally:
            if sess.get("proc") is proc:
                sess["proc"] = None

        clean_out = ANSI_RE.sub("", raw_out or "")
        clean_err = clean_powershell_stderr(raw_err or "", cmd)
        exit_code = proc.returncode if proc.returncode is not None else 0

        out_lines = []
        for line in clean_out.splitlines(keepends=True):
            stripped_line = line.strip()
            if stripped_line.startswith(CWD_SENTINEL):
                candidate = stripped_line[len(CWD_SENTINEL):].strip()
                if os.path.isdir(candidate):
                    sess["prev_cwd"] = sess["cwd"]
                    sess["cwd"] = candidate
            elif stripped_line.startswith(EXIT_SENTINEL):
                try:
                    exit_code = int(stripped_line[len(EXIT_SENTINEL):].strip())
                except ValueError:
                    pass
            else:
                out_lines.append(line)

        final_out = "".join(out_lines)
        if len(final_out) > 200000:
            final_out = final_out[:200000] + "\n... [output truncated at 200 KB]\n"
        if len(clean_err) > 50000:
            clean_err = clean_err[:50000] + "\n... [stderr truncated]\n"

        return {
            "ok": exit_code == 0,
            "stdout": final_out,
            "stderr": clean_err,
            "exit_code": exit_code,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }
    except Exception as exc:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Execution error: {exc}\n",
            "exit_code": 1,
            "cwd": sess["cwd"],
            "duration_ms": int((time.time() - t0) * 1000),
        }


def complete_terminal_token(prefix: str, session_id: str = "default") -> List[str]:
    sess = get_term_session(session_id)
    cwd = sess["cwd"]
    token = prefix or ""
    matches: List[str] = []

    builtins = [
        "cargo", "rustc", "rustup", "python", "git", "ls", "dir", "cd", "pwd",
        "cat", "type", "mkdir", "rm", "cp", "mv", "touch", "echo",
        "whoami", "who am i", "user", "id", "hostname", "uname", "neofetch", "sysinfo",
        "date", "ipconfig", "ifconfig", "netsh", "ping", "clear", "help", "reset",
    ]
    if "\\" not in token and "/" not in token:
        for b in builtins:
            if b.startswith(token.lower()):
                matches.append(b)

    # File/dir completion in cwd
    base_dir = cwd
    name_prefix = token
    dir_part = ""
    if "/" in token or "\\" in token:
        sep = "\\" if "\\" in token else "/"
        dir_part, name_prefix = token.rsplit(sep, 1)
        candidate_dir = dir_part if os.path.isabs(dir_part) else os.path.join(cwd, dir_part)
        if os.path.isdir(candidate_dir):
            base_dir = candidate_dir
        else:
            return sorted(set(matches))[:20]

    try:
        for entry in os.listdir(base_dir):
            if entry.lower().startswith(name_prefix.lower()):
                full = os.path.join(base_dir, entry)
                suffix = "\\" if os.path.isdir(full) else ""
                rel = f"{dir_part}\\{entry}{suffix}" if dir_part else f"{entry}{suffix}"
                matches.append(rel)
    except Exception:
        pass

    return sorted(set(matches))[:25]


def trigger_wlan_scan() -> bool:
    """Trigger an active Windows hardware Wi-Fi scan via native wlanapi.dll."""
    global _LAST_SCAN_TIME
    if os.name != "nt":
        return False
    try:
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        class WLAN_INTERFACE_INFO(ctypes.Structure):
            _fields_ = [
                ("InterfaceGuid", GUID),
                ("strInterfaceDescription", ctypes.c_wchar * 256),
                ("isState", ctypes.c_uint),
            ]

        class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
            _fields_ = [
                ("dwNumberOfItems", ctypes.c_ulong),
                ("dwIndex", ctypes.c_ulong),
                ("InterfaceInfo", WLAN_INTERFACE_INFO * 1),
            ]

        wlan = ctypes.windll.wlanapi
        negotiated = ctypes.c_ulong()
        handle = ctypes.c_void_p()
        if wlan.WlanOpenHandle(2, None, ctypes.byref(negotiated), ctypes.byref(handle)) != 0:
            return False

        scanned = False
        try:
            plist = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()
            if wlan.WlanEnumInterfaces(handle, None, ctypes.byref(plist)) == 0:
                try:
                    if plist.contents.dwNumberOfItems > 0:
                        guid = plist.contents.InterfaceInfo[0].InterfaceGuid
                        rc = wlan.WlanScan(handle, ctypes.byref(guid), None, None, None)
                        scanned = (rc == 0)
                finally:
                    wlan.WlanFreeMemory(plist)
        finally:
            wlan.WlanCloseHandle(handle, None)

        if scanned:
            with _SCAN_LOCK:
                _LAST_SCAN_TIME = time.time()
        return scanned
    except Exception:
        return False


def run_cmd(args: List[str], timeout: int = 8) -> str:
    try:
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
        )
        return res.stdout or ""
    except Exception:
        return ""


def signal_pct_to_dbm(pct: int) -> int:
    # Standard Windows WLAN percentage (0..100) to approximate RSSI dBm (-100..-50)
    return int(round((pct / 2.0) - 100))


def subnet_mask_to_prefix(mask: str) -> Optional[int]:
    try:
        net = ipaddress.IPv4Network(f"0.0.0.0/{mask.strip()}", strict=False)
        return net.prefixlen
    except Exception:
        return None


def parse_wlan_interfaces(output: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "interface_name": "WiFi",
        "driver": "Wireless Network Adapter",
        "mac": "00:00:00:00:00:00",
        "state": "disconnected",
        "connected": False,
        "radio_on": True,
        "ssid": "",
        "bssid": "",
        "band": "",
        "channel": "",
        "radio_type": "",
        "authentication": "",
        "cipher": "",
        "receive_rate": "",
        "transmit_rate": "",
        "signal_pct": 0,
        "rssi_dbm": None,
        "profile": "",
    }

    if not output.strip():
        return info

    # Look for radio hardware/software off notices
    lower_out = output.lower()
    if "software off" in lower_out or "hardware off" in lower_out:
        info["radio_on"] = False

    field_map = {
        "name": "interface_name",
        "description": "driver",
        "physical address": "mac",
        "state": "state",
        "ssid": "ssid",
        "ap bssid": "bssid",
        "bssid": "bssid",
        "band": "band",
        "channel": "channel",
        "radio type": "radio_type",
        "authentication": "authentication",
        "cipher": "cipher",
        "receive rate (mbps)": "receive_rate",
        "transmit rate (mbps)": "transmit_rate",
        "signal": "signal",
        "rssi": "rssi",
        "profile": "profile",
    }

    for line in output.splitlines():
        if ":" not in line:
            continue
        key_raw, val_raw = line.split(":", 1)
        key = key_raw.strip().lower()
        val = val_raw.strip()

        if key in field_map:
            mapped = field_map[key]
            if mapped == "mac":
                info["mac"] = val.upper()
            elif mapped == "state":
                info["state"] = val.lower()
                info["connected"] = val.lower() == "connected"
            elif mapped == "signal":
                m = re.search(r"(\d+)", val)
                if m:
                    info["signal_pct"] = int(m.group(1))
            elif mapped == "rssi":
                m = re.search(r"(-?\d+)", val)
                if m:
                    info["rssi_dbm"] = int(m.group(1))
            elif mapped == "bssid":
                info["bssid"] = val.lower()
            elif mapped == "authentication":
                info["authentication"] = re.sub(r"\s+", " ", val)
            else:
                info[mapped] = val

    if info["rssi_dbm"] is None and info["signal_pct"] > 0:
        info["rssi_dbm"] = signal_pct_to_dbm(info["signal_pct"])

    return info


def parse_ipconfig(output: str, iface_name: str, driver: str, mac: str) -> Dict[str, Any]:
    net_info: Dict[str, Any] = {
        "host_name": socket.gethostname(),
        "ipv4": "N/A",
        "cidr": "N/A",
        "subnet_mask": "",
        "gateway": "N/A",
        "dns": [],
    }

    if not output.strip():
        return net_info

    host_match = re.search(r"Host Name[\s.]*:\s*(.+)", output)
    if host_match:
        net_info["host_name"] = host_match.group(1).strip()

    # Split ipconfig output into adapter sections
    sections = re.split(r"\r?\n(?=\S[^\r\n]*:\s*$)", output, flags=re.MULTILINE)
    target_section = None
    mac_dash = mac.replace(":", "-").upper()

    for sec in sections:
        header = sec.splitlines()[0].strip() if sec.splitlines() else ""
        if f"Wireless LAN adapter {iface_name}:" in header:
            target_section = sec
            break
    if target_section is None and mac_dash and mac_dash != "00-00-00-00-00-00":
        for sec in sections:
            if mac_dash in sec.upper():
                target_section = sec
                break
    if target_section is None and driver:
        for sec in sections:
            if driver.lower() in sec.lower():
                target_section = sec
                break

    if not target_section:
        return net_info

    lines = target_section.splitlines()
    current_field = None
    gateways: List[str] = []
    dns_list: List[str] = []

    for line in lines:
        if ":" in line and re.match(r"^\s+[A-Za-z0-9]", line):
            left, right = line.split(":", 1)
            field = re.sub(r"[.\s]+$", "", left.strip()).lower()
            val = right.strip()
            current_field = field

            if field == "ipv4 address":
                ip_m = re.search(r"(\d+\.\d+\.\d+\.\d+)", val)
                if ip_m:
                    net_info["ipv4"] = ip_m.group(1)
            elif field == "subnet mask":
                mask_m = re.search(r"(\d+\.\d+\.\d+\.\d+)", val)
                if mask_m:
                    net_info["subnet_mask"] = mask_m.group(1)
            elif field == "default gateway" and val:
                gateways.append(val)
            elif field == "dns servers" and val:
                dns_list.append(val)
        elif current_field in ("default gateway", "dns servers") and line.strip():
            val = line.strip()
            if current_field == "default gateway":
                gateways.append(val)
            else:
                dns_list.append(val)

    # Prefer IPv4 gateway & DNS
    ipv4_gw = [g for g in gateways if re.match(r"^\d+\.\d+\.\d+\.\d+$", g)]
    if ipv4_gw:
        net_info["gateway"] = ipv4_gw[0]
    elif gateways:
        net_info["gateway"] = gateways[0]

    ipv4_dns = [d for d in dns_list if re.match(r"^\d+\.\d+\.\d+\.\d+$", d)]
    net_info["dns"] = ipv4_dns if ipv4_dns else dns_list

    if net_info["ipv4"] != "N/A":
        prefix = subnet_mask_to_prefix(net_info["subnet_mask"]) if net_info["subnet_mask"] else None
        net_info["cidr"] = f"{net_info['ipv4']}/{prefix}" if prefix is not None else net_info["ipv4"]

    return net_info


def parse_saved_profiles(output: str) -> List[str]:
    profiles: List[str] = []
    for line in output.splitlines():
        m = re.match(r"^\s*All User Profile\s*:\s*(.+)$", line)
        if m:
            profiles.append(m.group(1).strip())
    return profiles


def parse_visible_networks(
    output: str, connected_ssid: str, connected_info: Dict[str, Any], saved_profiles: List[str]
) -> List[Dict[str, Any]]:
    networks_by_ssid: Dict[str, Dict[str, Any]] = {}
    saved_set = set(saved_profiles)

    current_ssid: Optional[str] = None
    current_auth = "Unknown"
    current_enc = ""
    current_bssid_data: Optional[Dict[str, Any]] = None

    def commit_bssid() -> None:
        nonlocal current_bssid_data
        if not current_ssid or not current_bssid_data:
            return
        existing = networks_by_ssid.get(current_ssid)
        sig = current_bssid_data.get("signal_pct", 0)
        is_conn_bssid = (
            connected_info.get("connected")
            and current_ssid == connected_ssid
            and current_bssid_data.get("bssid", "") == connected_info.get("bssid", "")
        )
        if existing is None or is_conn_bssid or (not existing.get("_matched_bssid") and sig > existing.get("signal_pct", -1)):
            networks_by_ssid[current_ssid] = {
                "ssid": current_ssid,
                "authentication": current_auth,
                "encryption": current_enc,
                "signal_pct": sig,
                "rssi_dbm": signal_pct_to_dbm(sig) if sig > 0 else -90,
                "radio_type": current_bssid_data.get("radio_type", "802.11"),
                "band": current_bssid_data.get("band", ""),
                "channel": current_bssid_data.get("channel", ""),
                "bssid": current_bssid_data.get("bssid", ""),
                "connected": bool(connected_info.get("connected") and current_ssid == connected_ssid),
                "saved": current_ssid in saved_set,
                "_matched_bssid": is_conn_bssid,
            }

    for line in output.splitlines():
        ssid_m = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", line.strip())
        if ssid_m:
            commit_bssid()
            current_bssid_data = None
            raw_ssid = ssid_m.group(1).strip()
            current_ssid = raw_ssid if raw_ssid else None
            current_auth = "Unknown"
            current_enc = ""
            continue

        if current_ssid is None:
            continue

        bssid_m = re.match(r"^\s*BSSID\s+\d+\s*:\s*(.+)$", line)
        if bssid_m:
            commit_bssid()
            current_bssid_data = {
                "bssid": bssid_m.group(1).strip().lower(),
                "signal_pct": 0,
                "radio_type": "",
                "band": "",
                "channel": "",
            }
            continue

        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip().lower()
        val = v.strip()

        if current_bssid_data is None:
            if key == "authentication":
                current_auth = val
            elif key == "encryption":
                current_enc = val
        else:
            if key == "signal":
                sm = re.search(r"(\d+)", val)
                if sm:
                    current_bssid_data["signal_pct"] = int(sm.group(1))
            elif key == "radio type":
                current_bssid_data["radio_type"] = val
            elif key == "band":
                current_bssid_data["band"] = val
            elif key == "channel":
                current_bssid_data["channel"] = val

    commit_bssid()

    # Ensure the currently connected SSID is always present and uses live interface stats
    if connected_info.get("connected") and connected_ssid:
        networks_by_ssid[connected_ssid] = {
            "ssid": connected_ssid,
            "authentication": connected_info.get("authentication") or "Secured",
            "encryption": connected_info.get("cipher") or "",
            "signal_pct": connected_info.get("signal_pct", 0),
            "rssi_dbm": connected_info.get("rssi_dbm"),
            "radio_type": connected_info.get("radio_type") or "802.11ax",
            "band": connected_info.get("band") or "",
            "channel": connected_info.get("channel") or "",
            "bssid": connected_info.get("bssid") or "",
            "connected": True,
            "saved": True,
        }

    result = []
    for item in networks_by_ssid.values():
        item.pop("_matched_bssid", None)
        result.append(item)

    # Sort: connected network first, then saved networks / strongest signal
    result.sort(key=lambda n: (not n["connected"], -n["signal_pct"], n["ssid"].lower()))
    return result


def collect_wifi_snapshot() -> Dict[str, Any]:
    iface_out = run_cmd(["netsh", "wlan", "show", "interfaces"])
    iface = parse_wlan_interfaces(iface_out)

    ip_out = run_cmd(["ipconfig", "/all"])
    ip_info = parse_ipconfig(ip_out, iface["interface_name"], iface["driver"], iface["mac"])

    profiles_out = run_cmd(["netsh", "wlan", "show", "profiles"])
    saved_profiles = parse_saved_profiles(profiles_out)

    nets_out = run_cmd(["netsh", "wlan", "show", "networks", "mode=bssid"])
    networks = parse_visible_networks(nets_out, iface["ssid"], iface, saved_profiles)

    return {
        "live": True,
        "timestamp": int(time.time()),
        "interface": iface,
        "network_config": ip_info,
        "networks": networks,
        "saved_profiles": saved_profiles,
    }


def run_ping_diagnostic(target: str) -> Dict[str, Any]:
    if not target or target == "N/A":
        target = "1.1.1.1"
    # Allow only valid IP addresses or clean hostnames
    if not re.match(r"^[A-Za-z0-9.\-:]+$", target):
        target = "1.1.1.1"

    out = run_cmd(["ping", "-n", "3", "-w", "1500", target], timeout=10)
    avg_m = re.search(r"Average\s*=\s*(\d+ms)", out, flags=re.IGNORECASE)
    min_m = re.search(r"Minimum\s*=\s*(\d+ms)", out, flags=re.IGNORECASE)
    max_m = re.search(r"Maximum\s*=\s*(\d+ms)", out, flags=re.IGNORECASE)
    loss_m = re.search(r"\((\d+%)\s*loss\)", out, flags=re.IGNORECASE)

    avg_ms = avg_m.group(1) if avg_m else "N/A"
    min_ms = min_m.group(1) if min_m else "N/A"
    max_ms = max_m.group(1) if max_m else "N/A"
    loss = loss_m.group(1) if loss_m else "100%"
    ok = avg_m is not None and loss != "100%"

    return {
        "ok": ok,
        "target": target,
        "min": min_ms,
        "avg": avg_ms,
        "max": max_ms,
        "loss": loss,
        "raw": out.strip(),
    }


class WifiBridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Silence noisy console logs for clean background execution
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in ("/", "/index.html", "/MicroOS_Desktop.html"):
            if os.path.exists(INDEX_HTML_PATH):
                with open(INDEX_HTML_PATH, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
            else:
                self._send_json({"error": "index.html not found"}, status=404)
            return

        if path == "/api/health":
            self._send_json({"ok": True, "service": "joydev-micro-os-wifi-bridge", "port": PORT})
            return

        if path == "/api/wifi":
            if query.get("rescan", ["0"])[0] == "1":
                if trigger_wlan_scan():
                    time.sleep(1.8)
            else:
                # Periodically trigger a non-blocking scan so nearby AP list stays fresh
                now = time.time()
                if now - _LAST_SCAN_TIME > 30.0:
                    threading.Thread(target=trigger_wlan_scan, daemon=True).start()
            self._send_json(collect_wifi_snapshot())
            return

        if path == "/api/wifi/ping":
            snap = collect_wifi_snapshot()
            gateway = snap["network_config"].get("gateway", "1.1.1.1")
            result = run_ping_diagnostic(gateway)
            result["receive_rate"] = snap["interface"].get("receive_rate", "")
            result["transmit_rate"] = snap["interface"].get("transmit_rate", "")
            result["ssid"] = snap["interface"].get("ssid", "")
            self._send_json(result)
            return

        if path == "/api/term/state":
            sid = query.get("session", ["default"])[0]
            sess = get_term_session(sid)
            self._send_json(
                {
                    "ok": True,
                    "session": sid,
                    "cwd": sess["cwd"],
                    "project_root": PROJECT_ROOT,
                    "user": os.environ.get("USERNAME", "joydev"),
                    "host": socket.gethostname(),
                    "running": sess.get("proc") is not None,
                }
            )
            return

        if path == "/api/term/complete":
            sid = query.get("session", ["default"])[0]
            prefix = query.get("prefix", [""])[0]
            self._send_json({"ok": True, "matches": complete_terminal_token(prefix, sid)})
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            body = {}

        if path == "/api/wifi/connect":
            ssid = str(body.get("ssid", "")).strip()
            if not ssid:
                self._send_json({"ok": False, "message": "Missing SSID"}, status=400)
                return

            snap = collect_wifi_snapshot()
            saved = set(snap.get("saved_profiles", []))
            iface_name = snap["interface"].get("interface_name", "WiFi")

            if ssid not in saved:
                self._send_json(
                    {
                        "ok": False,
                        "message": f"'{ssid}' does not have a saved Windows Wi-Fi profile yet. Connect to it once in Windows Wi-Fi settings to save its credentials.",
                        "snapshot": snap,
                    }
                )
                return

            out = run_cmd(["netsh", "wlan", "connect", f"name={ssid}", f"interface={iface_name}"])
            time.sleep(1.5)
            new_snap = collect_wifi_snapshot()
            ok = "successfully" in out.lower() or new_snap["interface"].get("ssid") == ssid
            self._send_json({"ok": ok, "message": out.strip() or f"Connection requested for '{ssid}'.", "snapshot": new_snap})
            return

        if path == "/api/wifi/disconnect":
            snap = collect_wifi_snapshot()
            iface_name = snap["interface"].get("interface_name", "WiFi")
            out = run_cmd(["netsh", "wlan", "disconnect", f"interface={iface_name}"])
            time.sleep(0.8)
            new_snap = collect_wifi_snapshot()
            self._send_json({"ok": True, "message": out.strip() or "Disconnected.", "snapshot": new_snap})
            return

        if path == "/api/term/exec":
            sid = str(body.get("session", "default"))
            command = str(body.get("command", ""))
            result = execute_terminal_command(command, sid)
            self._send_json(result)
            return

        if path == "/api/term/cancel":
            sid = str(body.get("session", "default"))
            sess = get_term_session(sid)
            proc = sess.get("proc")
            if proc is not None:
                kill_proc_tree(proc.pid)
                sess["proc"] = None
                self._send_json({"ok": True, "message": "Running process terminated."})
            else:
                self._send_json({"ok": True, "message": "No active process."})
            return

        self._send_json({"error": "Not found"}, status=404)


class ReusableThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def is_already_running() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=0.4):
            return True
    except OSError:
        return False


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--dump":
        print(json.dumps(collect_wifi_snapshot(), indent=2))
        return

    if is_already_running():
        # Another bridge instance is already serving localhost:8765
        return

    try:
        server = ReusableThreadingHTTPServer((HOST, PORT), WifiBridgeHandler)
    except OSError:
        return

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
