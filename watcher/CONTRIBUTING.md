# Contributing

In order to test this component, you need:
- a test Zimfarm instance with a username + password
- a test S3 bucket  (compliance must NOT be activated on this bucket)
- credentials to access this bucket (keyId and secretAccessKey suggested below)
- Docker

Rebuild the Docker image:

```
docker build -t local-zf-watcher .
```

Export the secret `S3_URL` as environment variable. Note that the S3 URL starts with `https`.


On Bash/Zsh shells (replace `<your_s3_host_name>`, `<your_key_id>`, `<your_secret_access_key>` and `<your_bucket>` with proper values):

```
 export S3_URL="https://<your_s3_host_name>/?keyId=<your_key_id>&secretAccessKey=<your_secret_access_key>&bucketName=<your_bucket>"
```

Run a test (here my zimfarm is running in docker on a container `backend` in network `zimfarm_default`, adapt command to your local setup):
```
docker run -it --rm -e ZIMFARM_API_URL=http://backend:8000/v1 -e S3_URL=$S3_URL --network zimfarm_default local-zf-watcher watcher --zimfarm-username admin --zimfarm-password admin --only tezos.stackexchange.com --runonce
```