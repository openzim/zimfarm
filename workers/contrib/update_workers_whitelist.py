#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Update Zimfarm IP whitelist

    Updates the Kiwix Wasabi S3 Policy in use by zimfarm-worker to change the list
    of IP adresses allowed to access it.

    Requires:
        pip install "kiwixstorage>=0.1,<1.0"
    Usage:
        # edit script first to adjust workers list
        ./update_workers_whitelist.py "https://s3.wasabisys.com/?keyId=<keyId>&secretAccessKey=<secretAccessKey>"
    """

import os
import sys
import json
import pathlib

from kiwixstorage import KiwixStorage

POLICY_ARN = "arn:aws:iam::100000050990:policy/ZimfarmWorker"
STATEMENT_ID = "ZimfarmWorkersIPsWhiteList"

workers_path = "workers.json"
try:
    with open(pathlib.Path(__file__).parent.joinpath(workers_path), "r") as fh:
        WORKERS = json.load(fh)
except IOError:
    try:
        url = (
            "https://raw.githubusercontent.com/openzim/zimfarm/master"
            "/workers/contrib/workers.json"
        )
        import requests

        WORKERS = requests.get(url).json()
    except ImportError:
        print(f"{workers_path} not present, you'll need requests to fetch from github")
        sys.exit(1)
    except Exception as exc:
        print(f"{workers_path} not present. couldn't fetch from github at {url}: {exc}")
        sys.exit(1)
except Exception as exc:
    print(f"Failed to read {workers_path}: {exc}")
    sys.exit(1)


def get_statement():
    return {
        "Sid": "ZimfarmWorkersIPsWhiteList",
        "Effect": "Deny",
        "Action": "s3:*",
        "Resource": "arn:aws:s3:::*",
        "Condition": {"NotIpAddress": {"aws:SourceIp": list(WORKERS.values())}},
    }


def main(url=None):
    if url is None:
        url = os.getenv("S3URL")
    if not url:
        print("Missing URL.")
        sys.exit(1)

    s3 = KiwixStorage(url=url)
    if not s3.check_credentials(list_buckets=True, failsafe=False):
        print("credentials not OK")
        sys.exit(1)

    print("credentials OK")

    iam = s3.get_service("iam")

    versions = iam.list_policy_versions(PolicyArn=POLICY_ARN).get("Versions", [])
    print(f"We have {len(versions)} for {POLICY_ARN}")
    version_id = None
    for version in versions:
        if version["IsDefaultVersion"]:
            version_id = version["VersionId"]

    print(f"Default version is {version_id}")

    # delete all other versions
    if len(versions) == 5:
        print("Deleting all other versions…")
        for version in versions:
            if version["VersionId"] == version_id:
                continue
            print(f"Deleting version {version['VersionId']}")
            iam.delete_policy_version(
                PolicyArn=POLICY_ARN, VersionId=version["VersionId"]
            )

    if not version_id:
        print("Existing policy doesn't exist. probably a mistake?")
        sys.exit(1)

    pv = (
        iam.get_policy_version(PolicyArn=POLICY_ARN, VersionId=version_id)
        .get("PolicyVersion", {})
        .get("Document")
    )
    if not pv:
        print("We don't have a policy document.")
        sys.exit(1)

    print(f"Current Policy:")
    from pprint import pprint as pp

    pp(pv)

    statement = get_statement()  # gen new statement

    try:
        stmt_index = [s["Sid"] for s in pv["Statement"]].index(STATEMENT_ID)
        pv["Statement"][stmt_index] = statement
    except ValueError:
        pv["Statement"].append(statement)

    new_policy = json.dumps(pv, indent=4)
    print(f"New Policy:\n{new_policy}")

    print("Overwriting policy…")
    iam.create_policy_version(
        PolicyArn=POLICY_ARN, PolicyDocument=new_policy, SetAsDefault=True
    )


if __name__ == "__main__":
    main(*sys.argv[1:])
