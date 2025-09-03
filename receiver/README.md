# zim-receiver

Zimfarm-authenticated SSH server for scp uploads

# Usage

```bash
docker run -p 1622:22 \
    -v /data/warehouse/zim:/jail/zim:rw \
    -v /data/zim:/mnt/zim:rw \
    -v /data/quarantine:/mnt/quarantine:rw \
    -v /data/check_logs:/mnt/check_logs:rw
    ghcr.io/openzim/zimfarm-receiver
```

# Components

## SSH Server

A dedicated SSH server to serve for ZIM and logs files uploads using SCP.

- Additional SSH server chrooted into `/jail`
- Configured to authenticate only via the Zimfarm API using `get_zimfarm_key`
- Using `uploader` user, with an rssh shell.
- Supports both SCP and SFTP.

## ZIM Quarantaine

A file events watcher that moves incoming ZIM files to final location after a successful check

- Running every minute on `/jail/zim` via a cron task
- Moving files to `/mnt/zim` if file is not in the root of the source directory, `/mnt/quarantine` otherwise.

Previously, it used `zimcheck` from libzim tools to check that ZIMs are valid and move them to quarantine folder if check fails. Now, it just checks that they are in appropriate
subfolder and moves them to final destination.

### Volumes

You should define several volumes when you run the container :

- The ZIMs dir to check : `-v <YOUR_ZIM_DIRECTORY_TO_CHECK>:/jail/zim`
- The valids ZIMs dir : `-v <YOUR_ZIM_DIRECTORY>:/mnt/zim`
- The quarantine dir : `-v <YOUR_ZIM_QUARANTINE_DIRECTORY>:/mnt/quarantine`
