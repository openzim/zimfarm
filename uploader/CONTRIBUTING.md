# Contributing

In order to test this component, you need:
- Docker
- a test Zimfarm instance with a username + password (below we use the one from `dev` folder Docker compose stack)
- a test SSH host (below we use the one from `dev` folder Docker compose stack)
- a test S3 bucket on Wasabi (you will have to set compliance to fully test the uploader)
- credentials to access this bucket (keyId and secretAccessKey suggested below)

Rebuild the Docker image:

```
docker build -t local-zf-uploader .
```

## S3 tests

Export the secret `S3_URL` as environment variable. Note that the S3 URL starts with `s3`.


On Bash/Zsh shells (replace `<your_s3_host_name>`, `<your_key_id>`, `<your_secret_access_key>` and `<your_bucket>` with proper values):

```
 export S3_URL="s3://<your_s3_host_name>/?keyId=<your_key_id>&secretAccessKey=<your_secret_access_key>&bucketName=<your_bucket>"
```

Run a test without compliance activated on the bucket:

```
docker run -it --rm -v $PWD:/data local-zf-uploader uploader --file /data/CONTRIBUTING.md --upload-uri $S3_URL
```

Run same test twice, it should work.

Delete the file from the bucket and activate compliance (with a 1 day setting for instance).

Run a test which will set the object compliance:

```
docker run -it --rm -v $PWD:/data local-zf-uploader uploader --file /data/CONTRIBUTING.md --upload-uri $S3_URL --delete-after 30
```

It should succeed. If you run the same test a second time, it will fail due to compliance (HTTP 400 error).

## SCP test

Following test upload should succeed.

```
docker run -it --rm -v $PWD:/data -v $PWD/dev/test_worker-identity/id_rsa:/etc/ssh/keys/id_rsa --network zimfarm_default local-zf-uploader uploader --file /data/CONTRIBUTING.md --upload-uri scp://uploader@receiver:22/logs/CONTRIBUTING.md --move
```

## SFTP test

Following test upload should succeed.

```
docker run -it --rm -v $PWD/CONTRIBUTING.md:/data/CONTRIBUTING.md -v $PWD/dev/test_worker-identity/id_rsa:/etc/ssh/keys/id_rsa --network zimfarm_default local-zf-uploader uploader --file /data/CONTRIBUTING.md --upload-uri sftp://uploader@receiver:22/logs/CONTRIBUTING.md
```