## Healthcheck

This service monitors the status of Zimfarm services and components and displays results as HTML

### Environment variables

- ZIMFARM_API_URL: Zimfarm backend API URL.
- ZIMFARM_USERNAME: Username to authenticate with on Zimfarm.
- ZIMFARM_PASSWORD: Password of user to authenticate with on Zimfarm.
- ZIMFARM_DATABASE_URL: Zimfarm database connection URL, including the driver, user credentials, host and port e.g `postgresql+psycopg://zimfarm:zimpass@postgresdb:5432/zimfarm`.
