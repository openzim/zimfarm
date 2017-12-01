# Warehouse

The ftp server accepting uploads from zimfarm workers

## How to run

1. close this repo
2. change directory to warehouse: `cd warehouse`
3. (optional) customize Dockerfile, see guide below
4. build container and run `docker build -t warehouse .`
5. run container
```
docker run -p 21:21 -p 28011-28090:28011-28090 \
           -v /files:/files \
           -e FTP_COMMAND_PORT=21 \
           -e FTP_DATA_PORT_RANGE=28011-28090 \
           -e TOKEN_VALIDATION_URL=https://farm.openzim.org/api/auth/validate \
           -e MASQUERADE_ADDRESS=163.172.33.162 \
           warehouse
```


Example:
```
docker build -t warehouse . &&
docker run -p 21:21 -p 28011-28090:28011-28090 \
           -v /files:/files \
           -e FTP_COMMAND_PORT=21 \
           -e FTP_DATA_PORT_RANGE=28011-28090 \
           -e TOKEN_VALIDATION_URL=https://farm.openzim.org/api/auth/validate \
           -e MASQUERADE_ADDRESS=163.172.33.162 \
           warehouse
```

## Environment Variables

| Env                  | Default     | Description                                                                     |
|----------------------|-------------|---------------------------------------------------------------------------------|
| FTP_COMMAND_PORT     | 21          | command port inside container                                                   |
| FTP_DATA_PORT_RANGE  | 28011-28090 | data port range inside container                                                |
| TOKEN_VALIDATION_URL |             | url used to validate file uploading token                                       |
| MASQUERADE_ADDRESS   |             | IP address in PASV reply, set when warehouse is running behind a NAT or gateway |
| FILE_STORAGE_DIR     | /files      | the directory where all zim files are stored inside the container               |