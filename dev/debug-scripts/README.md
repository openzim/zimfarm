
This folder contains one debug script `two-tasks-same-schedule.py` which was used to reproduce [issue 813](https://github.com/openzim/zimfarm/issues/813).

This script works **only** with companion modifications on the current branch.

## How to
- Start docker compose stack (see [upper README.md](../README.md) for details)
```
docker compose -p zimfarm up
```
- Run debug script from inside the zf-backend container
```
docker exec -it zf_backend python debug-scripts/two-tasks-same-schedule.py
```
- Stop docker compose stack
```
docker compose -p zimfarm down
```
