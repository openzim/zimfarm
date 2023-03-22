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
- upload the file to our S3 bucket with a Metadata for the version
- delete the local file we downloaded
- schedule matching recipe(s) on the Zimfarm as we now have updated dumps


**Note**: check source-code for up-to-date behavior
