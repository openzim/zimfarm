zimfarm-watcher
===============

[![Docker](https://ghcr-badge.deta.dev/openzim/zimfarm-watcher/latest_tag?label=docker)](https://ghcr.io/openzim/zimfarm-watcher)

Watch StackExchange dump files repository for updates to download/upload all

StackExchange dump repository, hosted by Archive.org is refreshed twice a year.
Archive.org's mirrors are all very slow to download from.

To speed-up sotoki's scrapes, we need to mirror this folder on a faster server.

This tool runs forever and checks periodically for those dumps on the main server.

Should there be an update, this tool would (for each file):
- compute its version as YYYY-MM based on file modification time
- check whether we have this version in our S3 bucket
- check whether zimfarm is currently using the current dump and skip in that case
- check whether there's a pending task for this dump and delete it in that case
- if we had the same file but for another version, we'd delete it from bucket
- test the downloaded archive's integrity and discard it if it is corrupted
- upload the file to our S3 bucket with a Metadata for the version
- delete the local file we downloaded
- schedule matching recipe(s) on the Zimfarm as we now have updated dumps


**Note**: check source-code for up-to-date behavior

## Recovering from a corrupted archive on S3

If a recipe keeps failing to extract its StackExchange dump, the archive mirrored on
our S3 bucket might be corrupted (e.g. from a previous download of a flaky
Archive.org mirror, before the integrity check above was added). Since the watcher
only re-downloads a file when its `lastmodified` metadata differs from the one on
Archive.org, simply running it again will not fix an already-corrupted file: as far
as the watcher is concerned, it's already in sync.

To force the watcher to redownload, re-test and re-upload a specific domain's
archive regardless of its current sync status, use `--only <domain>` together with
`--force` (this combination is required: `--force` alone is rejected):

```
docker run -it --rm -e ZIMFARM_API_URL=... -e S3_URL=$S3_URL local-zf-watcher \
  watcher --only tezos.stackexchange.com --force --runonce
```

`--only` can be repeated to force multiple domains in the same run.
