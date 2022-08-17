# maintenance scripts

Scripts for some zimfarm-db maintenance we do manually.

Most expects an environment variable with the URL/credentials to the DB and [`pymongo`](https://pypi.org/project/pymongo/)

```sh
pip install pymongo
export ZF_MONGO_URI="mongodb://login:password@somehost:21017/Zimfarm"
./update_scraper_version.py sotoki dev
```
