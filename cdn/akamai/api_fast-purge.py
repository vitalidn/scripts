"""
Usage:
    script.py (--cpc | --url) DATA... [--delete] [--stage]
    script.py (-h | --help)
    script.py --version
   
Examples:
    script.py -c 12345 67890
    script.py -u http://my-cdn.playtika.com/path/ https://my-cdn.playtika.com/path2/

Options:
    -c --cpc        Purge cache by CP Code(s) list.
    -u --url        Purge cache by URL/ARL list.
    -d --delete     Use Delete method to purge cache. Default: Invalidate.
    -s --stage      Purge in Stage network, instead of Production.
    -h --help       Show this screen.
    --version       Show version.

A protocol is required, for example, http:// or https://.
In most cases, regardless of whether http or https protocol is specified,
both versions are purged when either is submitted.
If you know that your configuration uses different cache keys for each protocol,
or if you see issues with stale content for the https requests after purging,
then use an ARL to purge the https version of the object.
https://techdocs.akamai.com/purge-cache
"""

from akamai.edgegrid import EdgeGridAuth, EdgeRc
from docopt import docopt
import json
import requests

edgerc = EdgeRc("~/.edgerc")
section = "default"

with requests.Session() as session:
    session.headers = {"Content-Type": "application/json", "Accept": "application/json"}
    session.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    session.verify = False

host = edgerc.get(section, "host")


def purge_cache(cpc, url, delete, stage, data):
    if cpc:
        invalidate_by = "cpcode"
    if url:
        invalidate_by = "url"
    if delete:
        invalidate_methot = "delete"
    else:
        invalidate_methot = "invalidate"
    if stage:
        network = "staging"
    else:
        network = "production"
    print("network", network)
    url = f"https://{host}/ccu/v3/{invalidate_methot}/{invalidate_by}/{network}"
    payload = {"objects": data}
    response = session.post(url, json=payload)
    if response.ok:
        data = response.json()
        print(json.dumps(data, indent=4))
    else:
        print("Url:", url)
        print("payload:", payload)
        print("Status code:", response.status_code, "with output:")
        print(response.text)


if __name__ == "__main__":
    arg = docopt(__doc__, version=1.0)
    print(arg)

    purge_cache(
        arg["--cpc"],
        arg["--url"],
        arg["--delete"],
        arg["--stage"],
        arg["DATA"]
    )
