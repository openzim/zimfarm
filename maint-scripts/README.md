# maintenance scripts

Scripts for some zimfarm-db maintenance we do manually.

Most expects an environment variable with the URL/credentials to the DB and [`pymongo`](https://pypi.org/project/pymongo/)

```sh
pip install -r requirements.txt
 export POSTGRES_URI="postgresql+psycopg://login:password@somehost:5432/zimfarm"
PYTHONPATH=../dispatcher/backend/src/ ./update_scraper_version.py sotoki dev
```
