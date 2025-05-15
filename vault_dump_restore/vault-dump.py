#!/usr/bin/env python

from __future__ import print_function
import datetime
import os
import sys
import json

import hvac

client = hvac.Client()

def is_secret_latest_version_deleted(path, mountpoint):
    metadata = client.secrets.kv.v2.read_secret_metadata(path, mount_point=mountpoint)['data']
    deletion_time = metadata['versions'][str(metadata['current_version'])]['deletion_time']
    return deletion_time != ''


def get_secret_data(path, mountpoint):
    # ignore secrets that are marked as deleted (but not destroyed), don't bother backing up old versions
    if is_secret_latest_version_deleted(path, mountpoint):
        return None

    content = client.secrets.kv.v2.read_secret_version(path, mount_point=mountpoint)['data']['data']

    secret_data = {}
    for key in content:
        secret_data[key] = content[key]

    return secret_data


def recurse_secrets(path_prefix, mountpoint):
    sys.stderr.write("Recursing into path prefix \"{0}\"\n".format(path_prefix))
    secrets_data = {}
    keys = client.secrets.kv.v2.list_secrets(path_prefix, mount_point=mountpoint)['data']['keys']
    for key in keys:
        item_path = path_prefix + key
        if key.endswith('/'):
            secrets_data.update(recurse_secrets(item_path, mountpoint))
        else:
            secret_data = get_secret_data(item_path, mountpoint)
            if secret_data:
                secrets_data[item_path] = secret_data
    return secrets_data


vault_dump_mountpoint = os.environ.get('VAULT_DUMP_MOUNTPOINT', '/settings/')
vault_dump_path_prefix = os.environ.get('VAULT_DUMP_PATH_PREFIX', '')
output_file_path = os.environ.get('VAULT_DUMP_JSON_FILE', 'secrets.json')

print('#')
print('# vault-dump-kv2.py backup')
print("# backup date: {} UTC".format(datetime.datetime.utcnow()))
print("# VAULT_DUMP_MOUNTPOINT setting: {}".format(vault_dump_mountpoint))
print("# VAULT_DUMP_PATH_PREFIX setting: {}".format(vault_dump_path_prefix))
print("# Output JSON File: {}".format(output_file_path))
print('# STDIN encoding: {}'.format(sys.stdin.encoding))
print('# STDOUT encoding: {}'.format(sys.stdout.encoding))
print('#')
print('# WARNING: not guaranteed to be consistent!')

secrets_data = recurse_secrets(vault_dump_path_prefix, vault_dump_mountpoint)

# Save secrets data to a JSON file
with open(output_file_path, 'w') as json_file:
    json.dump(secrets_data, json_file, indent=2)

print("# Secrets saved to JSON file: {}".format(output_file_path))
