# maintenance scripts

Scripts for some zimfarm-db maintenance we do manually.

## Running from you machine

Most script expects an environment variable with the URL/credentials to the DB and appropriate PYTHONPATH

```sh
pip install -r requirements.txt
 export POSTGRES_URI="postgresql+psycopg://login:password@somehost:5432/zimfarm"
PYTHONPATH=../src/ ./update_scraper_version.py sotoki dev
```

## Running from inside the API container

Scripts are also deployed in production in the dispatcher backend container, where you can run them directly.

```sh
PYTHONPATH=/app /app/maint-scripts/update_scraper_version.py sotoki dev
```