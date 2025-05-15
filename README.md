# Scripts for automating SRE/DevOps tasks

This repository contains various utility scripts for system administration tasks.

## Available Scripts

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
