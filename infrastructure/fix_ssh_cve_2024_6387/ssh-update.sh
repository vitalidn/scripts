#!/bin/bash

_os_version=$(lsb_release -rs | awk -F'.' '$0=$1')

function update () {
if [[ $_os_version -gt 20 ]]; then
	export DEBIAN_FRONTEND=noninteractive
        apt-get update && apt-get install -yq --only-upgrade openssh-server openssh-client
else
        echo "Ubuntu is $_os_version, nothing to do"
fi
}

update
