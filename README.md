# Scripts for automating SRE/DevOps tasks

This repository contains various utility scripts for system administration tasks.

## Available Scripts

### SSH CVE-2024-6387 Fix
Location: `infrastructure/fix_ssh_cve_2024_6387/`
- Script to fix the OpenSSH signal handler race condition vulnerability
- Supports multiple hosts processing
- Includes verification of fix application
- Provides detailed logging of changes
- [More details](infrastructure/fix_ssh_cve_2024_6387/README.md)

### Akamai Cache Purge
Location: `cdn/akamai/`
- Script for purging Akamai CDN cache via API
- Supports both CP Codes and URL-based purging
- Configurable for Production and Staging environments
- Provides detailed API response logging
- [More details](cdn/akamai/README.md)

### Vault Dump and Restore
Location: `vault_dump_restore/`
- Python scripts for backing up and restoring HashiCorp Vault secrets
- Supports KV v2 secrets engine
- Includes LDAP authentication
- Allows searching through dumped secrets
- [More details](vault_dump_restore/README.md)

### Interactive Disk Partitioning
Location: `interactive_disks_partition/`
- Interactive script for partitioning multiple disks across multiple hosts
- Supports host ranges (e.g., host[1:5])
- Creates identical partition layouts across all specified hosts
- Features safety checks and detailed logging
- [More details](interactive_disks_partition/README.md)

### Sysctl Configuration
Location: `config_sysctl_args/`
- Batch configuration of sysctl parameters on remote hosts
- Supports parallel processing of multiple hosts
- Verifies parameter existence and applies changes
- Uses YAML configuration file for parameter definitions
- [More details](config_sysctl_args/README.md)

### DNS Suffix Management
Location: `fixing_resolv.conf/`
- Validates and fixes DNS search suffixes on Linux nodes
- Updates DOMAINS entry in systemd network interface files
- Supports parallel processing of multiple nodes
- Includes safety checks and verification steps
- [More details](fixing_resolv.conf/README.md)

## Common Features
- All scripts support parallel processing of multiple hosts
- SSH-based remote execution
- Detailed logging and error handling
- Interactive prompts for user input
- Safety checks to prevent accidental system modifications

## Requirements

- Python 3.x
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scripts
```

2. Install dependencies for each script separately by following the instructions in their respective README files.

## Project Structure

```
scripts/
├── README.md
├── infrastructure/
│   └── fix_ssh_cve_2024_6387/
│       ├── README.md
│       └── fix_ssh_cve_2024_6387.py
├── cdn/
│   └── akamai/
│       ├── README.md
│       └── api_fast-purge.py
├── vault_dump_restore/
│   ├── README.md
│   └── vault_dump_restore.py
├── interactive_disks_partition/
│   ├── README.md
│   └── interactive_disks_partition.py
├── config_sysctl_args/
│   ├── README.md
│   └── config_sysctl_args.py
├── fixing_resolv.conf/
│   ├── README.md
│   └── fixing_resolv.conf.py
└── ...
```

## Usage

Each script has its own README file with detailed usage instructions. Navigate to the respective directory for more information.

## License

MIT License
