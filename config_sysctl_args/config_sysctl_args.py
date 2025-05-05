#!/usr/bin/env python3

import argparse
import getpass
import logging
import re
import shlex
import subprocess
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

# SSH options with multiplexing for speed
SSH_OPTS = "-o BatchMode=yes -o ControlMaster=auto -o ControlPersist=60s"

def run_ssh_script(node: str, script: str) -> Tuple[int, List[str], List[str]]:
    cmd = ["ssh"] + shlex.split(SSH_OPTS) + [node, "bash", "-s"]
    proc = subprocess.run(
        cmd,
        input=script,
        text=True,
        capture_output=True
    )
    return proc.returncode, proc.stdout.splitlines(), proc.stderr.splitlines()

def parse_node(mask: str) -> List[str]:
    m = re.fullmatch(r"^(.+)-\[(\d{1,4}):(\d{1,4})\](\..+)$", mask)
    if not m:
        raise ValueError(
            "Mask must be in the format prefix-[start:end].suffix"
        )
    prefix, start_s, end_s, suffix = m.groups()
    start, end = int(start_s), int(end_s)
    if start > end:
        raise ValueError("Start of range must not exceed end")

    pad = len(start_s) == len(end_s) and start_s.startswith("0")
    fmt = f"{{:0{len(start_s)}d}}" if pad else "{}"
    return [f"{prefix}-{fmt.format(i)}{suffix}" for i in range(start, end + 1)]


def read_config(filepath: Path) -> List[dict]:
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file {filepath} not found")
    data = yaml.safe_load(filepath.read_text())
    if not isinstance(data, dict) or "sysctl_args" not in data:
        raise ValueError("YAML must contain the 'sysctl_args' key")
    return data["sysctl_args"]


def process_node(node: str, settings: List[dict], sudo_pw: str) -> Tuple[str, List[str], str]:
    logs: List[str] = []
    pw_esc = shlex.quote(sudo_pw)

    read_cmd = f"echo {pw_esc} | sudo -S -p '' cat /etc/sysctl.conf"
    rc, conf_lines, err_lines = run_ssh_script(node, read_cmd)
    if rc != 0:
        return node, [], f"Failed to read sysctl.conf: {' '.join(err_lines)}"
    conf_text = "\n".join(conf_lines)

    for item in settings:
        key = item["name"]
        val = str(item["value"])

        check_sys_path = key.replace('.', '/')
        check_cmd = f"test -e /proc/sys/{check_sys_path}"
        rc_check, _, _ = run_ssh_script(node, check_cmd)
        if rc_check != 0:
            logs.append(f"[{node}] SKIPPING: {key} (not available in /proc/sys)")
            continue

        logs.append(f"[{node}] CHECKING: {key}")

        pattern = rf"^{re.escape(key)}=(.*)$"
        if re.search(pattern, conf_text, flags=re.MULTILINE):
            logs.append(f"[{node}] Key: {key} exists, updating to {val}")
            cmd_conf = (
                f"echo {pw_esc} | sudo -S -p '' "
                f"sed -i 's|^{key}=.*|{key}={val}|' /etc/sysctl.conf"
            )
        else:
            logs.append(f"[{node}] Key: {key} not found, appending {val}")
            cmd_conf = (
                f"echo {pw_esc} | sudo -S -p '' "
                f"bash -c \"echo '{key}={val}' >> /etc/sysctl.conf\""
            )
        rc2, _, err2 = run_ssh_script(node, cmd_conf)
        if rc2 != 0:
            logs.append(f"[{node}] ERROR saving {key} in config: {' '.join(err2)}")
        else:
            logs.append(f"[{node}] Saved in config: {key}={val}")

        apply_cmd = f"echo {pw_esc} | sudo -S -p '' sysctl -w {key}={val}"
        rc3, out3, err3 = run_ssh_script(node, apply_cmd)
        if rc3 != 0:
            logs.append(f"[{node}] ERROR applying {key}: {' '.join(err3)}")
        else:
            logs.append(f"[{node}] Applied: {key}={val}")

        verify_cmd = f"sysctl -n {shlex.quote(key)}"
        rc4, out4, err4 = run_ssh_script(node, verify_cmd)
        if rc4 == 0 and out4:
            logs.append(f"[{node}] VERIFIED: {key} = {out4[0].strip()} ✔️")
        else:
            logs.append(f"[{node}] Verification failed for {key}: {' '.join(err4)}")

    return node, logs, ""


def keyscan_known_hosts(hosts: List[str]) -> None:
    print(f"[keyscan] Starting SSH key scan for {len(hosts)} hosts…")
    known_hosts_path = Path.home() / ".ssh" / "known_hosts"
    for host in hosts:
        try:
            result = subprocess.run(
                ["ssh-keyscan", "-H", host],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout:
                with known_hosts_path.open("a") as f:
                    f.write(result.stdout)
        except Exception as e:
            logging.warning(f"Failed to scan SSH key for {host}: {e}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify & apply sysctl settings")
    p.add_argument(
        "--max-hosts", "-j",
        type=int, default=4,
        help="Parallel SSH hosts (default: 4)"
    )
    return p.parse_args()


def prompt_user() -> Tuple[List[str], str, List[dict]]:
    mask = input("Enter hosts (e.g. prefix-[1:100].domain): ").strip()
    hosts = parse_node(mask)
    sudo_pw = getpass.getpass("Enter sudo password: ")
    settings = read_config(Path.cwd() / "new_sysctl_args.yaml")
    return hosts, sudo_pw, settings


def setup_keyscan(hosts: List[str]) -> None:
    keyscan_known_hosts(hosts)


def run_on_hosts(
        hosts: List[str], settings: List[dict], sudo_pw: str, max_hosts: int
) -> dict[str, bool]:
    summary: dict[str, bool] = {}
    parallel_hosts = max(1, min(max_hosts, len(hosts)))
    print(f"\nProcessing: {len(hosts)} hosts with parallel {parallel_hosts} host(s)…")
    with ThreadPoolExecutor(max_workers=parallel_hosts) as pool:
        fut2host = {
            pool.submit(process_node, host, settings, sudo_pw): host
            for host in hosts
        }
        for fut in as_completed(fut2host):
            host = fut2host[fut]
            try:
                _, out_lines, errs = fut.result()
                for line in out_lines:
                    print(line)
                if errs:
                    print(f"[{host}] ERRORS: {errs}")
                    summary[host] = False
                else:
                    summary[host] = True
            except Exception as e:
                print(f"[{host}] EXCEPTION: {e}")
                summary[host] = False
    return summary


def print_summary(summary: dict[str, bool]) -> None:
    succ = sum(summary.values())
    total = len(summary)
    print(f"\nSummary: {succ}/{total} succeeded.")


def main() -> None:
    args = parse_args()
    try:
        hosts, sudo_pw, settings = prompt_user()
    except Exception as e:
        print(f"Error: {e}")
        return

    setup_keyscan(hosts)
    summary = run_on_hosts(hosts, settings, sudo_pw, args.max_hosts)
    print_summary(summary)


if __name__ == "__main__":
    main()
