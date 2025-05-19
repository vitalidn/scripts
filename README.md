# Scripts Collection

A collection of useful scripts for various tasks.

## Contents

### Infrastructure
- [SSH CVE-2024-6387 Fix](infrastructure/fix_ssh_cve_2024_6387/README.md) - Script to fix the OpenSSH signal handler race condition vulnerability (CVE-2024-6387)

### CDN
- [Akamai Cache Purge](cdn/akamai/README.md) - Script for purging Akamai CDN cache via API

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
└── ...
```

## Usage

Each script has its own README file with detailed usage instructions. Navigate to the respective directory for more information.

## License

MIT License
