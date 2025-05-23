#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple
"""
./fixing_resolv_conf_cli.py \
  --node-mask PREFIX-[01:111] \
  --dns-suffix bingo.ca1 \
  --sudo-password your_sudo_password \
  --max-workers 8

"""

# SSH options with multiplexing for speed
SSH_OPTS = "-o BatchMode=yes -o ControlMaster=auto -o ControlPersist=60s"

def run_command(cmd: str) -> Tuple[int, str, str]:
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def parse_node_mask(mask: str) -> List[str]:
    m = re.fullmatch(r"(.+)-\[(\d{1,4}):(\d{1,4})\]", mask)
    if not m:
        raise ValueError("Mask must look like PREFIX-[01:111]")

    prefix, start_s, end_s = m.groups()
    start, end = int(start_s), int(end_s)
    if start > end:
        raise ValueError("Range start must not exceed range end")

    pad = len(start_s) == len(end_s) and start_s.startswith("0")
    if pad:
        fmt = f"{{:0{len(start_s)}d}}"
        return [f"{prefix}-{fmt.format(i)}" for i in range(start, end + 1)]
    return [f"{prefix}-{i}" for i in range(start, end + 1)]


def prime_known_hosts(fqdns: List[str]) -> None:
    nodelist = " ".join(map(shlex.quote, fqdns))
    rc, out, err = run_command(f"ssh-keyscan -T 3 -t rsa,ed25519 {nodelist} 2>/dev/null")
    if rc != 0 or not out:
        print(f"[keyscan] warning: {err or 'no keys collected'}")
        return

    kh_path = Path.home() / ".ssh" / "known_hosts"
    kh_path.parent.mkdir(parents=True, exist_ok=True)
    existing = set(kh_path.read_text().splitlines()) if kh_path.exists() else set()

    if new_lines:
        with kh_path.open("a") as fh:
            fh.write("\n".join(new_lines) + "\n")
        print(f"[keyscan] Scanned {len(fqdns)} hosts, added {len(new_hosts)} new host(s) ({len(new_lines)} key lines) to {kh_path}")
    else:
        print(f"[keyscan] scanned {len(fqdns)} hosts; all keys already present; skipping")


def process_node(node: str, dns_suffix: str, sudo_pw: str) -> Tuple[bool, str]:
    logs: list[str] = []
    fqdn = f"{node}.{dns_suffix}"
    logs.append(f"[{node}] SSH to {fqdn}")

    rc, stdout, err = run_command(f"ssh {SSH_OPTS} {fqdn} cat /etc/resolv.conf")
    if rc != 0:
        logs.append(f"[{node}] SSH/read error: {err}")
        return False, "\n".join(logs)

    search_line = next((l for l in stdout.splitlines() if l.startswith("search")), None)
    if not search_line:
        logs.append(f"[{node}] no 'search' line — skip")
        return True, "\n".join(logs)

    current = search_line.split()[-1]
    if current.lower() == dns_suffix.lower():
        logs.append(f"[{node}] DOMAINS already {dns_suffix}")
        return True, "\n".join(logs)

    rc, g_out, g_err = run_command(
        f"ssh {SSH_OPTS} {fqdn} grep -i {shlex.quote(current)} /run/systemd/netif/links/*"
    )
    if rc != 0 or not g_out:
        logs.append(f"[{node}] link file not found: {g_err or 'pattern not found'}")
        return False, "\n".join(logs)

    link_num = g_out.split("/run/systemd/netif/links/")[1].split(":")[0]
    link_file = f"/run/systemd/netif/links/{link_num}"

    remote_cmd = (
        f"echo {shlex.quote(sudo_pw)} | sudo -S sed -i 's/^DOMAINS=.*/DOMAINS={dns_suffix}/' {link_file}"
    )
    rc, _, sed_err = run_command(f"ssh {SSH_OPTS} {fqdn} {shlex.quote(remote_cmd)}")
    if rc == 0:
        logs.append(f"[{node}] DOMAINS fixed: {current} → {dns_suffix}")
        return True, "\n".join(logs)

    logs.append(f"[{node}] sudo error: {sed_err or 'no stderr'}")
    return False, "\n".join(logs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify & fix DNS DOMAINS setting across multiple nodes"
    )
    parser.add_argument(
        "--node-mask", "-m", required=True,
        help="Node range mask, e.g. PREFIX-[01:111]"
    )
    parser.add_argument(
        "--dns-suffix", "-d", required=True,
        help="Required DNS suffix, e.g. bingo.ca1"
    )
    parser.add_argument(
        "--sudo-password", "-p", required=True,
        help="Sudo password for remote commands"
    )
    parser.add_argument(
        "--max-workers", "-w", type=int, default=4,
        help="Parallel SSH workers (default: 4)"
    )
    args = parser.parse_args()

    try:
        nodes = parse_node_mask(args.node_mask)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    dns_suffix = args.dns_suffix.strip()
    sudo_pw = args.sudo_password

    prime_known_hosts([f"{n}.{dns_suffix}" for n in nodes])

    workers = max(1, min(args.max_workers, len(nodes)))
    print(f"\nProcessing {len(nodes)} nodes with {workers} worker(s)…")

    summary: dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fut2node = {pool.submit(process_node, n, dns_suffix, sudo_pw): n for n in nodes}
        for fut in as_completed(fut2node):
            node = fut2node[fut]
            try:
                ok, log_block = fut.result()
                print(log_block, flush=True)
                summary[node] = ok
            except Exception as exc:
                summary[node] = False
                print(f"[{node}] EXCEPTION: {exc}")

    ok_total = sum(summary.values())
    print(f"\nSummary: {ok_total}/{len(nodes)} nodes processed successfully.")


if __name__ == "__main__":
    main()
