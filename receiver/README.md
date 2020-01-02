zim-receiver
====

Zimfarm-authenticated SSH server for scp uploads with ZIM validator

# Usage

``` bash
docker run -p 1622:22 \
    -v /data/warehouse/zim:/jail/zim:rw \
    -v /data/warehouse/logs:/jail/logs:rw \
    -v /data/zim:/mnt/zim:rw \
    -v /data/quarantine:/mnt/quarantine:rw \
    -v /data/check_logs:/mnt/check_logs:rw \
    --env ZIMCHECK_OPTION="-A"
    openzim/zimfarm-receiver
```

# Components

## SSH Server

A dedicated SSH server to serve for ZIM and logs files uploads using SCP.

* Additional SSH server chrooted into `/jail`
* Configured to authenticate only via the Zimfarm API using `get_zimfarm_key`
* Using `uploader` user, with an rssh shell.
* Supports both SCP and SFTP.

## ZIM Quarantaine

A file events watcher that moves incoming ZIM files to final location after a successful check

* Using `zimcheck` from the libzim tools
* Running every minute on `/jail/zim` via a cron task
* Moving valid files to `/mnt/zim` and invalid ones to `/mnt/quarantine`
* `zimcheck` outputs logs in `/mnt/check_logs`.

### Volumes

You should define several volumes when you run the container :

* The ZIMs dir to check : `-v <YOUR_ZIM_DIRECTORY_TO_CHECK>:/jail/zim`
* The valids ZIMs dir : `-v <YOUR_ZIM_DIRECTORY>:/mnt/zim`
* The quarantine dir : `-v <YOUR_ZIM_QUARANTINE_DIRECTORY>:/mnt/quarantine`
* The log dir : `-v <YOUR_LOG_DIRECTORY>:/mnt/check_logs`

### Options

You can set the variable `VALIDATION_OPTION` to change the behaviour :

* NO_CHECK = just move to the directory of valid zim
* NO_QUARANTINE = make the check (log) and move to the directory of valid zim  even if errors

You can also set `zimcheck` options with `ZIMCHECK_OPTION` environ:

```
-A , --all             run all tests. Default if no flags are given.
-C , --checksum        Internal CheckSum Test
-M , --metadata        MetaData Entries
-F , --favicon         Favicon
-P , --main            Main page
-R , --redundant       Redundant data check
-U , --url_internal    URL check - Internal URLs
-X , --url_external    URL check - Internal URLs
-E , --mime            MIME checks
-D , --details         Details of error
```

## Warehouse Keeper

**note**: to be implemented.

A file cleaner script for removing obsolete log files and changing log formatting

* Converts uploaded JSON logs to text logs on scraper_completed
* Removes log files for obsolete tasks
* Runs every hour via a cron task
