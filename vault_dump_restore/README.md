# Vault Dump and Restore Scripts

This directory contains Python scripts for backing up and restoring secrets from HashiCorp Vault KV v2 secrets engine.

## Prerequisites

- Python 3.x
- `hvac` Python package (HashiCorp Vault API client)
- Access to a HashiCorp Vault instance
- Proper Vault authentication configured (environment variables or token)

## How to Run the Scripts

### Dumping Vault Contents

To get Vault contents (for example, to find variables that are missing in repository):

1. Set the source Vault address:
```bash
export VAULT_ADDR=http://SRC_IP:8200
```

2. Login to Vault using LDAP:
```bash
vault login -method=ldap username=<user_name>
```

3. Run the dump script:
```bash
python vault-dump.py
```

The result will be saved locally to `secrets.json`. You can search through the dump using grep, for example:
```bash
grep -E -i '"[^"]*bucket[^"]*"' secrets.json
```

### Restoring Vault Contents

To restore the backup:

1. Set the destination Vault address:
```bash
export VAULT_ADDR=http://DST_IP:8200
```

2. Login to Vault using LDAP:
```bash
vault login -method=ldap username=byachmeniuk
```

3. Run the restore script:
```bash
python vault-restore.py
```

## Scripts

### vault-dump.py

This script dumps secrets from a Vault KV v2 secrets engine to a JSON file.

#### Usage

```bash
python vault-dump.py
```

#### Environment Variables

- `VAULT_DUMP_MOUNTPOINT`: The mount point of the KV v2 secrets engine (default: '/settings/')
- `VAULT_DUMP_PATH_PREFIX`: The path prefix to start dumping from (default: '')
- `VAULT_DUMP_JSON_FILE`: The output JSON file path (default: 'secrets.json')

#### Features

- Recursively dumps all secrets under the specified path prefix
- Skips deleted secrets (secrets marked for deletion but not destroyed)
- Saves secrets in a structured JSON format
- Includes metadata about the backup process

### vault-restore.py

This script restores secrets from a JSON file to a Vault KV v2 secrets engine.

#### Usage

```bash
python vault-restore.py
```

#### Environment Variables

- `VAULT_RESTORE_MOUNTPOINT`: The mount point of the KV v2 secrets engine (default: '/settings/')
- `VAULT_RESTORE_JSON_FILE`: The input JSON file path (default: 'secrets.json')

#### Features

- Restores secrets from a previously created JSON dump
- Requires explicit confirmation before restoring
- Shows the Vault URL before restoration
- Displays progress during restoration
- Includes host information in the output

## Example Workflow

1. Dump secrets from source Vault:
```bash
export VAULT_DUMP_MOUNTPOINT='/settings/'
export VAULT_DUMP_PATH_PREFIX=''
export VAULT_DUMP_JSON_FILE='secrets.json'
python vault-dump.py
```

2. Restore secrets to target Vault:
```bash
export VAULT_RESTORE_MOUNTPOINT='/settings/'
export VAULT_RESTORE_JSON_FILE='secrets.json'
python vault-restore.py
```

## Security Notes

- The JSON dump file contains sensitive information. Ensure proper access controls are in place.
- The scripts use the default Vault client configuration. Make sure proper authentication is set up.
- Consider encrypting the JSON dump file if storing it for an extended period.
- Review the secrets before restoration to ensure they are being restored to the correct location.

## Error Handling

- The restore script checks for the existence of the input JSON file
- Both scripts provide progress information through stderr
- The restore script requires explicit confirmation before proceeding
- Deleted secrets are automatically skipped during the dump process 