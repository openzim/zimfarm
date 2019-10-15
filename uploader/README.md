uploader
===

Dedicated container/script to upload files to openzim/kiwix warehouses.

Files are uploaded via SFTP (pubkey authentication) using cURL.


## Usage

``` sh
docker run -v ~/.ssh/id_rsa:/etc/ssh/keys/id_rsa:ro -v /path/:/path:rw \
	openzim/uploader \
	--file /path/my_file.zim \
	--upload-uri sftp://warehouse.farm.openzim.org/zim/ \
	--username rgaudin \
	--delete
```
