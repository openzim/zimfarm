uploader
===

Dedicated container/script to upload files to openzim/kiwix warehouses.

Files are uploaded via SFTP (pubkey authentication) or SCP using OpenSSH.


## Usage

* Use `scp://` for SCP upload
* Use `sftp://` for SFTP upload

``` sh
docker run -v ~/.ssh/id_rsa:/etc/ssh/keys/id_rsa:ro -v /path/:/path:rw \
	openzim/uploader \
	--file /path/my_file.zim \
	--upload-uri sftp://uploader@warehouse.farm.openzim.org/zim/ \
    --move \
	--delete
```

### Parameters

* `--username`: if your URI has no username, you can specify it here.
* `--move`: upload to a temporary filename (`<fname>.tmp`) and rename it upon completion. Note that SCP is not able to do it so it uploads an `<fname>.complete` file upon completion instead.
* `--delete`: delete source file once uploaded successfuly.
* `--compress`: enable transfer compression.
* `--bandwidth`: enable bandwidth limit. Set it in Kbps.
