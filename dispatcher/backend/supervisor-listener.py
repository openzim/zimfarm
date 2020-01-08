#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" supervisor event listenner for generic script launching

    launches a script (passed as $1+) and communicates with supervisor """

import sys
import pathlib
import subprocess


def to_supervisor(text):
    # only eventlistener protocol messages may be sent to stdout
    sys.stdout.write(text)
    sys.stdout.flush()


def to_log(text):
    sys.stderr.write(text)
    sys.stderr.flush()


def main(command, args=[]):
    while True:
        # transition from ACKNOWLEDGED to READY
        to_supervisor("READY\n")

        # read header line and print it to stderr
        line = sys.stdin.readline()

        # read event payload and print it to stderr
        headers = dict([x.split(":") for x in line.split()])
        sys.stdin.read(int(headers["len"]))

        script = subprocess.run(
            [command] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        to_log(script.stdout)

        # if script.returncode != 0:
        #     to_supervisor("RESULT 4\nFAIL")

        # transition from READY to ACKNOWLEDGED
        to_supervisor("RESULT 2\nOK")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        to_log("no script specified, crashing")
        sys.exit(1)

    args = sys.argv[1:]
    if not pathlib.Path(args[0]).exists():
        to_log("script path `{cmd}` doesnt exists. crashing")
        sys.exit(1)

    main(args[0], args[1:])
