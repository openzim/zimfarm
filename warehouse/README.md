# Warehouse

The sftp server accepting uploads from zimfarm workers. 

Docker image: `docker pull openzim/zimfarm-warehouse`

When offliners finished running on workers, files are transported to warehouse using SFTP. 
Worker's identity is validated by public key authentication. 
Upon receiving auth challenge, warehouse send http request to dispatcher to validate public key.

Workers can:
- create directories
- list contents in a directory
- create and upload files
- get or change attributes of files or directories

Workers can not:
- delete directories and files
- follow or create links


## Environment Variables

| Env       | Default        | Description                                                  |
|-----------|----------------|--------------------------------------------------------------|
| RSA_KEY   |                | Server's RSA private key, will be generated if not specified |
| PORT      | 22             | Port the SFTP server will be listening                       |
| ROOT_PATH | /zim_files     | Path where the SFTP server will be severing from             |
| LOG_PATH  | /warehouse.log | SFTP server log                                              |

## Example

```bash
docker pull openzim/zimfarm-warehouse && \
docker run \
    -v /zim_files:/zim_files \
    -v /logs/warehouse.log:/warehouse.log \
    -p 1522:22 \
    -d \
    --name zimfarm_warehouse \
    openzim/zimfarm-warehouse
```