# Config Sysctl Batch Script

This script allows you to batch-check, update, and apply sysctl parameters on remote hosts via SSH. For each setting, the script:
1. Verifies that the corresponding `/proc/sys` path exists.
2. Updates or appends the entry in `/etc/sysctl.conf`.
3. Immediately applies the setting using `sysctl -w key=value`.
4. Verifies that the value has been successfully changed.

If a parameter is not available (the file in `/proc/sys/...` is missing), the script outputs:
```
[<node>] SKIPPING: <key> (not available in /proc/sys)
```
and moves on to the next setting.

---

## Requirements

- Python 3.7+
- PyYAML package installed:
  ```bash
  pip install pyyaml
  ```
- SSH access to target hosts with `sudo` privileges that do not require a password for reading and writing `/etc/sysctl.conf` and applying `sysctl -w`.

---

## Configuration File

Place a `sysctl_args.yaml` file in your working directory with the following structure:

```yaml
sysctl_args:
  - name: vm.max_map_count
    value: 524288
  - name: net.ipv6.conf.all.disable_ipv6
    value: 1
  # etc.
```

Each entry in the array should include:
- `name`: the sysctl key
- `value`: the desired value

---

## Usage

```bash
./batch_sysctl.py [--max-hosts N]
```

1. The script will prompt you for:
    - A host mask (format: `prefix-[start:end].suffix`, e.g., `rd-prod-tf-k8s-kafka-[1:5].rd.va2`).
    - Your sudo password.
2. It will run `ssh-keyscan` to add host keys to `~/.ssh/known_hosts`.
3. It will process hosts in parallel (default up to 4 at a time) and:
    - Apply each parameter individually with `sysctl -w`.
4. At the end, you will see a summary:

```
Summary: X/Y succeeded.
```

**Options**:
- `--max-hosts, -j`: maximum number of parallel SSH sessions (default: 4).

---

## Example

```bash
$ ./config_sysctl_args.py
Enter hosts (e.g. bingo-[1:100].domain): rd-prod-tf-k8s-kafka-[1:5].rd.va2
Enter sudo password: 
[keyscan] Starting SSH key scan for 5 hosts…

Processing: 5 hosts with parallel 4 host(s)…
[rd-prod-tf-k8s-kafka-1.rd.va2] CHECKING: vm.max_map_count
[rd-prod-tf-k8s-kafka-1.rd.va2] Key: vm.max_map_count exists, updating to 524288
[rd-prod-tf-k8s-kafka-1.rd.va2] Saved in config: vm.max_map_count=524288
[rd-prod-tf-k8s-kafka-1.rd.va2] Applied: vm.max_map_count=524288
[rd-prod-tf-k8s-kafka-1.rd.va2] VERIFIED: vm.max_map_count = 524288 ✔️
[rd-prod-tf-k8s-kafka-2.rd.va2] CHECKING: vm.max_map_count
[rd-prod-tf-k8s-kafka-2.rd.va2] Key: vm.max_map_count exists, updating to 524288
[rd-prod-tf-k8s-kafka-2.rd.va2] Saved in config: vm.max_map_count=524288
[rd-prod-tf-k8s-kafka-2.rd.va2] Applied: vm.max_map_count=524288
[rd-prod-tf-k8s-kafka-2.rd.va2] VERIFIED: vm.max_map_count = 524288 ✔️


Summary: 5/5 succeeded.
```

---

