# DNS Suffix Validator and Fixer for Linux Nodes


!!! DO NOT change it via netplan on active DC - it will lead to downtime.  
There is a bug in systemd-networkd (https://bugs.launchpad.net/ubuntu/+source/systemd/+bug/2003250) - changing configuration for bond interfaces impossible without downtime for now (either via netplan or directly via systemd).  
You can do it only with fixed systemd or via /run/systemd/netif/links/$id (where $id is id of network interface) state file.
This Python script checks and optionally fixes the `DOMAINS=` entry inside `/run/systemd/netif/links/*` files across a range of Linux nodes via SSH. It ensures all nodes use the expected DNS search suffix.


---

## ✨ Features

- **Interactive prompts** for node range, DNS suffix, and sudo password
- Automatically populates `~/.ssh/known_hosts` using `ssh-keyscan`
- Skips nodes where DNS suffix is already correct
- Updates `DOMAINS=` entry in the appropriate `link` file using `sudo + sed`
- **Parallel processing** of multiple nodes with configurable concurrency

---

## 📋 Requirements

- Python 3.7+
- SSH key-based access to all target nodes
- `sudo` access on target machines
- `ssh`, `ssh-keyscan`, `sed`, `grep` installed locally and remotely

No external Python packages required.

---

## 🔧 Usage

```bash
./fixing_resolv_conf.py [--max-workers N]
```

## Optional arguments

| Flag            | Default | Description                   |
| --------------- |---------| ----------------------------- |
| `--max-workers` | `4`     | Max parallel SSH connections. |

---

## 📘 Input Format

The script expects the node range in the format:
```
prefix-[start:end]
```

Examples:
- `node-[001:010]` ➜ `node-001`, `node-002`, ..., `node-010`
- `host-[5:7]` ➜ `host-5`, `host-6`, `host-7`

---

## 📤 What It Does

1. Builds full FQDNs for each node using the suffix provided
2. Uses `ssh-keyscan` to avoid "host key verification failed"
3. SSHes to each node to check `/etc/resolv.conf`
4. If current search domain is wrong:
   - Finds the appropriate `link` file in `/run/systemd/netif/links/`
   - Uses `sudo sed` to change `DOMAINS=...` line to the correct value
5. Prints a success/failure summary for all nodes

---

## ⚠️ Notes

- Does **not** support password-based SSH — only SSH keys
- Requires remote `sudo` to accept password via stdin
- Will modify remote system files — use with caution

---


## 🧪 Example session

```text
$ python fixing_resolv_conf.py

Enter node range (e.g. PREFIX-[01:111]): rd-prod-worker-[1:9]
Enter DNS suffix (e.g. bingo.ca1): rd.ca1
Enter sudo password: ********

Processing 9 nodes with up to 4 parallel worker(s)…

[rd-prod-worker-1] Connecting to rd-prod-worker-1.rd.ca1 …
[rd-prod-worker-1] DOMAINS updated: ca1 → rd.ca1
…
Summary: 9/9 nodes processed successfully.
```

