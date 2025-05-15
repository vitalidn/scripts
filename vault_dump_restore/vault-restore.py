#!/usr/bin/env python

import os
import sys
import json
import socket

import hvac

# Source: https://hvac.readthedocs.io/en/stable/usage/secrets_engines/kv_v2.html
client = hvac.Client()


def restore_secrets(secrets_data, mountpoint):
    for secret_path, secret_data in secrets_data.items():
        sys.stderr.write("Restoring secret at path: {}\n".format(secret_path))
        client.secrets.kv.v2.create_or_update_secret(secret_path, secret_data, mount_point=mountpoint)
        sys.stderr.write("Restored secret at path: {}\n".format(secret_path))

def get_current_host():
    return socket.gethostname()

vault_restore_mountpoint = os.environ.get('VAULT_RESTORE_MOUNTPOINT', '/settings/')
input_file_path = os.environ.get('VAULT_RESTORE_JSON_FILE', 'secrets.json')

if not os.path.exists(input_file_path):
    print("Error: Input JSON file not found at path: {}".format(input_file_path))
    sys.exit(1)

print('#')
print('# vault-restore-kv2.py restore')
print("# Current Host: {}".format(get_current_host()))
print("# VAULT_RESTORE_MOUNTPOINT setting: {}".format(vault_restore_mountpoint))
print("# Input JSON File: {}".format(input_file_path))
print('#')

# Load secrets data from the JSON file
with open(input_file_path, 'r') as json_file:
    secrets_data = json.load(json_file)

# Prompt the user for confirmation
print(f'VAULT URL: {client.url}')
confirmation = input("Do you want to restore the secrets to Vault? (yes/no): ")
if confirmation.lower() != "yes":
    print("Aborted. No changes made.")
    sys.exit(0)

restore_secrets(secrets_data, vault_restore_mountpoint)

print("# Secrets successfully restored to Vault.")
