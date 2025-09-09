#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

"""supervisor event listenner for generic script launching

launches a script (passed as $1+) and communicates with supervisor"""

import datetime
import pathlib
import subprocess
import sys


def to_supervisor(text: str):
    # only eventlistener protocol messages may be sent to stdout
    sys.stdout.write(text)
    sys.stdout.flush()


def to_log(text: str):
    sys.stderr.write(text)
    sys.stderr.flush()


def main(interval: int, command: str, args: list[str] | None = None):
    last_run: datetime.datetime | None = None
    args = args or []
    while True:
        # transition from ACKNOWLEDGED to READY
        to_supervisor("READY\n")

        # read header line and print it to stderr
        line = sys.stdin.readline()

        # read event payload and print it to stderr
        headers = dict([x.split(":") for x in line.split()])
        sys.stdin.read(int(headers["len"]))

        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        if last_run is None or last_run <= now - datetime.timedelta(seconds=interval):
            last_run = now
            script = subprocess.run(
                [command, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
            to_log(script.stdout)

        # if script.returncode != 0:
        #     to_supervisor("RESULT 4\nFAIL")

        # transition from READY to ACKNOWLEDGED
        to_supervisor("RESULT 2\nOK")


if __name__ == "__main__":
    if len(sys.argv) < 3:  # noqa: PLR2004
        to_log("missing interval and/or script, crashing")
        sys.exit(1)

    try:
        interval = int(sys.argv[1])
    except Exception:
        to_log(f"incorrect interval `{sys.argv[1]}, crashing")
        sys.exit(1)

    args = sys.argv[2:]
    if not pathlib.Path(args[0]).exists():
        to_log("script path `{cmd}` doesnt exists. crashing")
        sys.exit(1)

    main(interval, args[0], args[1:])
