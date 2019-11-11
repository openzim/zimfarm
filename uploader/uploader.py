#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import sys
import urllib
import logging
import pathlib
import argparse
import tempfile
import subprocess

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

CURL_BIN_PATH = pathlib.Path(os.getenv("CURL_BIN_PATH", "/usr/bin/curl"))
CURL_ERRORS = {
    1: "Unsupported protocol. This build of curl has no support for this protocol.: ",
    2: "Failed to initialize.: ",
    3: "URL malformed. The syntax was not correct.: ",
    4: "A feature or option that was needed to perform the desired request was not enabled or was explicitly disabled at build-time. To make curl able to do this, you probably need another build of libcurl!: ",
    5: "Couldn't resolve proxy. The given proxy host could not be resolved.: ",
    6: "Couldn't resolve host. The given remote host was not resolved.: ",
    7: "Failed to connect to host.: ",
    8: "Weird server reply. The server sent data curl couldn't parse.: ",
    9: "FTP access denied. The server denied login or denied access to the particular resource or directory you wanted to reach. Most often you tried to change to a directory that doesn't exist on the server.: ",
    10: "FTP accept failed. While waiting for the server to connect back when an active FTP session is used, an error code was sent over the control connection or similar.: ",
    11: "FTP weird PASS reply. Curl couldn't parse the reply sent to the PASS request.: ",
    12: "During an active FTP session while waiting for the server to connect back to curl, the timeout expired.: ",
    13: "FTP weird PASV reply, Curl couldn't parse the reply sent to the PASV request.: ",
    14: "FTP weird 227 format. Curl couldn't parse the 227-line the server sent.: ",
    15: "FTP can't get host. Couldn't resolve the host IP we got in the 227-line.: ",
    16: "HTTP/2 error. A problem was detected in the HTTP2 framing layer. This is somewhat generic and can be one out of several problems, see the error message for details.: ",
    17: "FTP couldn't set binary. Couldn't change transfer method to binary.: ",
    18: "Partial file. Only a part of the file was transferred.: ",
    19: "FTP couldn't download/access the given file, the RETR (or similar) command failed.: ",
    21: "FTP quote error. A quote command returned error from the server.: ",
    22: "HTTP page not retrieved. The requested url was not found or returned another error with the HTTP error code being 400 or above. This return code only appears if -f, --fail is used.: ",
    23: "Write error. Curl couldn't write data to a local filesystem or similar.: ",
    25: "FTP couldn't STOR file. The server denied the STOR operation, used for FTP uploading.: ",
    26: "Read error. Various reading problems.: ",
    27: "Out of memory. A memory allocation request failed.: ",
    28: "Operation timeout. The specified time-out period was reached according to the conditions.: ",
    30: "FTP PORT failed. The PORT command failed. Not all FTP servers support the PORT command, try doing a transfer using PASV instead!: ",
    31: "FTP couldn't use REST. The REST command failed. This command is used for resumed FTP transfers.: ",
    33: 'HTTP range error. The range "command" didn\'t work.: ',
    34: "HTTP post error. Internal post-request generation error.: ",
    35: "SSL connect error. The SSL handshaking failed.: ",
    36: "Bad download resume. Couldn't continue an earlier aborted download.: ",
    37: "FILE couldn't read file. Failed to open the file. Permissions?: ",
    38: "LDAP cannot bind. LDAP bind operation failed.: ",
    39: "LDAP search failed.: ",
    41: "Function not found. A required LDAP function was not found.: ",
    42: "Aborted by callback. An application told curl to abort the operation.: ",
    43: "Internal error. A function was called with a bad parameter.: ",
    45: "Interface error. A specified outgoing interface could not be used.: ",
    47: "Too many redirects. When following redirects, curl hit the maximum amount.: ",
    48: "Unknown option specified to libcurl. This indicates that you passed a weird option to curl that was passed on to libcurl and, rejected. Read up in the manual!: ",
    49: "Malformed telnet option.: ",
    51: "The peer's SSL certificate or SSH MD5 fingerprint was not OK.: ",
    52: "The server didn't reply anything, which here is considered an error.: ",
    53: "SSL crypto engine not found.: ",
    54: "Cannot set SSL crypto engine as default.: ",
    55: "Failed sending network data.: ",
    56: "Failure in receiving network data.: ",
    58: "Problem with the local certificate.: ",
    59: "Couldn't use specified SSL cipher.: ",
    60: "Peer certificate cannot be authenticated with known CA certificates.: ",
    61: "Unrecognized transfer encoding.: ",
    62: "Invalid LDAP URL.: ",
    63: "Maximum file size exceeded.: ",
    64: "Requested FTP SSL level failed.: ",
    65: "Sending the data requires a rewind that failed.: ",
    66: "Failed to initialise SSL Engine.: ",
    67: "The user name, password, or similar was not accepted and curl failed to log in.: ",
    68: "File not found on TFTP server.: ",
    69: "Permission problem on TFTP server.: ",
    70: "Out of disk space on TFTP server.: ",
    71: "Illegal TFTP operation.: ",
    72: "Unknown TFTP transfer ID.: ",
    73: "File already exists (TFTP).: ",
    74: "No such user (TFTP).: ",
    75: "Character conversion failed.: ",
    76: "Character conversion functions required.: ",
    77: "Problem with reading the SSL CA cert (path? access rights?).: ",
    78: "The resource referenced in the URL does not exist.: ",
    79: "An unspecified error occurred during the SSH session.: ",
    80: "Failed to shut down the SSL connection.: ",
    82: "Could not load CRL file, missing or wrong format (added in 7.19.0).: ",
    83: "Issuer check failed (added in 7.19.0).: ",
    84: "The FTP PRET command failed: ",
    85: "RTSP: mismatch of CSeq numbers: ",
    86: "RTSP: mismatch of Session Identifiers: ",
    87: "unable to parse FTP file list: ",
    88: "FTP chunk callback reported error: ",
    89: "No connection available, the session will be queued: ",
    90: "SSL public key does not matched pinned public key: ",
    91: "Invalid SSL certificate status.: ",
    92: "Stream error in HTTP/2 framing layer.: ",
}


def get_host_pub_md5(host, port):
    keyscan = subprocess.run(
        ["/usr/bin/ssh-keyscan", "-t", "rsa", "-p", str(port), host],
        capture_output=True,
        text=True,
    )
    if keyscan.returncode != 0:
        logger.error(f"unable to get remote host ({host}:{port}) public key")
        sys.exit(1)

    with tempfile.TemporaryFile() as keyscan_output:
        keyscan_output.write(keyscan.stdout.encode("ASCII"))
        keyscan_output.seek(0)

        keygen = subprocess.run(
            ["/usr/bin/ssh-keygen", "-l", "-E", "md5", "-f", "-"],
            capture_output=True,
            text=True,
            stdin=keyscan_output,
        )

    if keygen.returncode != 0:
        logger.error(f"unable to get fingerprint of host ({host}:{port}) public key")
        sys.exit(1)
    try:
        md5 = "".join(keygen.stdout.split(" ")[1].split(":")[1:])
    except Exception as exc:
        logger.error(f"error extracting md5 from fingerprint ({keygen.stdout}): {exc}")
        sys.exit(1)

    return md5


def extract_pubkey(private_key):
    """ extract public key from private key; save to a temp file, returning its path """
    keygen = subprocess.run(
        ["/usr/bin/ssh-keygen", "-y", "-f", str(private_key)],
        capture_output=True,
        text=True,
    )
    if keygen.returncode != 0:
        logger.error(f"unable to extract public key from private key ({private_key}")
        sys.exit(1)

    pubkey = tempfile.NamedTemporaryFile(mode="w", suffix=".pub", delete=False)
    pubkey.write(keygen.stdout)
    pubkey.close()
    return pathlib.Path(pubkey.name)


def upload_file(
    src_path, upload_uri, username, private_key, host_pub_md5, move=False, delete=False
):
    logger.info(f"Starting upload of {src_path}")
    public_key = extract_pubkey(private_key)

    # parse upload-uri so we can specify a temporary filename and rename upon success
    try:
        uri = urllib.parse.urlparse(upload_uri)
        uri_path = pathlib.Path(uri.path)
    except Exception as exc:
        logger.error(f"invalid upload URI: `{upload_uri}` ({exc}).")
        return 1

    if move:
        if uri.path.endswith("/"):
            final_fname = src_path.name
            temp_fname = f"{src_path.name}.tmp"
            upload_path = uri.path
            full_upload_uri = f"{upload_uri}{temp_fname}"
        else:
            final_fname = uri_path.name
            temp_fname = f"{final_fname}.tmp"
            upload_path = f"{uri_path.parent}/"
            full_upload_uri = f"{uri.scheme}://{uri.netloc}/{upload_path}/{temp_fname}"
    else:
        full_upload_uri = upload_uri

    args = [
        str(CURL_BIN_PATH),
        "--append",
        "--connect-timeout",
        "60",
        "--continue-at",
        "-",
        "--ipv4",
        "--retry-connrefused",
        "--retry-delay",
        "60",
        "--retry",
        "20",
        "--stderr",
        "-",
    ]

    if move:
        args += ["--quote", f"*rm {upload_path}{temp_fname}"]
        args += ["--quote", f"*rm {upload_path}{final_fname}"]
        args += [
            "--quote",
            f"-rename {upload_path}{temp_fname} {upload_path}{final_fname}",
        ]

    args += [
        "--hostpubmd5",
        host_pub_md5,
        "--pubkey",
        str(public_key),
        "--key",
        str(private_key),
        "--user",
        "{user}:".format(user=username),
        "--upload-file",
        str(src_path),
        full_upload_uri,
    ]

    logger.info("Executing: {args}\n".format(args=" ".join(args)))

    sys.exit(1)

    curl = subprocess.run(args=args, capture_output=True, text=True)

    if curl.returncode == 0:
        logger.info("Uploader ran successfuly.")
        if delete:
            logger.info("removing source file…")
            try:
                src_path.unlink()
            except Exception as exc:
                logger.error(f":: failed to remove ZIM file: {exc}")
            else:
                logger.info(":: success.")
    else:
        logger.error(
            "cURL failed returning {retcode}:: {msg}".format(
                retcode=curl.returncode,
                msg=CURL_ERRORS.get(curl.returncode, "Unknown error."),
            )
        )
    return curl.returncode


def main():
    parser = argparse.ArgumentParser(prog="uploader")

    parser.add_argument(
        "--file",
        help="absolute path to source file to upload",
        required=True,
        dest="src_path",
    )

    parser.add_argument(
        "--upload-uri",
        help="upload URI to upload to (folder, trailing-slash)",
        required=True,
        dest="upload_uri",
    )

    parser.add_argument(
        "--username",
        help="username to authenticate to warehouse",
        required=not bool(os.getenv("USERNAME")),
        default=os.getenv("USERNAME"),
    )

    parser.add_argument(
        "--key",
        help="path to RSA private key",
        dest="private_key",
        required=not bool(os.getenv("RSA_KEY", "/etc/ssh/keys/id_rsa")),
        default=os.getenv("RSA_KEY", "/etc/ssh/keys/id_rsa"),
    )

    parser.add_argument(
        "--move",
        help="whether to upload to a temp location and move to final one on success",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--delete",
        help="whether to delete source file upon success",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--debug",
        help="change logging level to DEBUG",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    # fail early if source file is not readable
    src_path = pathlib.Path(args.src_path).resolve()
    if (
        not src_path.exists()
        or not src_path.is_file()
        or not os.access(src_path, os.R_OK)
    ):
        logger.error(f"source file ({src_path}) doesn't exist or is not readable.")
        sys.exit(1)

    # fail early if private key is not readable
    private_key = pathlib.Path(args.private_key).resolve()
    if (
        not private_key.exists()
        or not private_key.is_file()
        or not os.access(private_key, os.R_OK)
    ):
        logger.error(
            f"private RSA key file ({private_key}) doesn't exist or is not readable."
        )
        sys.exit(1)

    # make sur upload-uri is correct (trailing slash)
    try:
        url = urllib.parse.urlparse(args.upload_uri)
    except Exception as exc:
        logger.error(f"invalid upload URI: `{args.upload_uri}` ({exc}).")
        sys.exit(1)
    else:
        if not url.path.endswith("/") and not pathlib.Path(url.path).suffix:
            logger.error(
                f"/!\\ your upload_uri doesn't end with a slash and has no file extension: `{args.upload_uri}`."
            )
            sys.exit(1)

    host_pub_md5 = get_host_pub_md5(url.hostname, url.port)

    # running upload
    sys.exit(
        upload_file(
            src_path=src_path,
            upload_uri=args.upload_uri,
            username=args.username,
            private_key=private_key,
            host_pub_md5=host_pub_md5,
            move=args.move,
            delete=args.delete,
        )
    )


if __name__ == "__main__":
    main()
