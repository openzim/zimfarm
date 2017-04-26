# ZIM Farm
A farm operated by bots to grow and harvest new zim files.

- Python 3.6
- flask (Web APIs)
- Celery (task Queue)
- RabbitMQ (broker)
- SQLite (task info & logs)

[Configuration Guide](https://github.com/kiwix/zimfarm/wiki/Configuration-Guide)

## Stage 1:

Goal: Create a queueing system that execute tasks when receiving request from a WebAPI. Specifically:

- [x] A SQLite database table to store all task info (name, type, shell command)
- [x] WebAPI: List All Templates `GET /templates/list`
- [x] WebAPI: Enqueue a task using template ID `POST tasks/enqueue/:template_id`
- [ ] WebAPI to add all tasks to the queue and execute them `POST tasks/enqueue_all`
- [ ] WebAPI to query current task queue progress, including: `POST tasks/status/:task_id`
  - [ ] how many tasks left
  - [ ] each task's status (`PENDING`, `EXECUTING`, `FINISHED`)
- [ ] Each task simply run shell scripts like `sleep(20)`

## Useful commands
- remove all containers: `docker rm $(docker ps -a -q)`
- remova all untagged images `docker rmi $(docker images -a | grep "^<none>" | awk "{print $3}")`