# Akamai Cache Purge Script

This script provides a command-line interface for purging content from Akamai CDN cache using either CP Codes or URLs.

## Features

- Purge cache by CP Codes
- Purge cache by URLs/ARLs
- Support for both Production and Staging networks
- Option to use either Invalidate or Delete purge methods
- JSON response output

## Prerequisites

- Python 3.x
- Required Python packages:
  - `akamai-edgegrid`
  - `docopt`
  - `requests`

## Installation

1. Install required packages:
```bash
pip install akamai-edgegrid docopt requests
```

2. Configure Akamai credentials:
   - Create or edit `~/.edgerc` file with your Akamai credentials
   - The file should contain a section named "default" with the following parameters:
     - host
     - client_token
     - client_secret
     - access_token

## Usage

### Basic Commands

Purge by CP Codes:
```bash
python api_fast-purge.py --cpc 12345 67890
```

Purge by URLs:
```bash
python api_fast-purge.py --url http://my-cdn.playtika.com/path/ https://my-cdn.playtika.com/path2/
```

### Options

- `-c, --cpc`: Purge cache by CP Code(s) list
- `-u, --url`: Purge cache by URL/ARL list
- `-d, --delete`: Use Delete method to purge cache (default: Invalidate)
- `-s, --stage`: Purge in Stage network (default: Production)
- `-h, --help`: Show help screen
- `--version`: Show version

### Important Notes

1. Protocol Requirements:
   - Always include the protocol (http:// or https://) in URLs
   - In most cases, both HTTP and HTTPS versions are purged when either is submitted
   - If your configuration uses different cache keys for each protocol, use ARL to purge HTTPS version specifically

2. Response:
   - The script outputs JSON response from Akamai API
   - In case of errors, it displays the request URL, payload, and error details

## Examples

1. Purge multiple CP Codes in production:
```bash
python api_fast-purge.py --cpc 12345 67890
```

2. Purge URLs in staging environment:
```bash
python api_fast-purge.py --url https://my-cdn.playtika.com/path/ --stage
```

3. Delete (instead of invalidate) URLs:
```bash
python api_fast-purge.py --url https://my-cdn.playtika.com/path/ --delete
```

## References

- [Akamai Purge Cache Documentation](https://techdocs.akamai.com/purge-cache) 