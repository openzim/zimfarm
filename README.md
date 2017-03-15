# ZIM Farm
A farm operated by bots to grow and harvest new zim files.

- Python 3.6
- flask (Web APIs)
- Celery (task Queue)
- RabbitMQ (boker)
- SQLite (task info & logs)

Config:
`pip3 install flask, flask_restful, Celery`

## Stage 1:
Goal: Create a queueing system that execute tasks when receiving request from a WebAPI. Specifically:

- A SQLite database table to store all task info (name, type, shell command)
- A WebAPI to add all tasks to the queue and execute them
- A WebAPI to query current task queue progress, including:
  - how many tasks left
  - each task's status (`PENDING`, `EXECUTING`, `FINISHED`)
- Each task simply run shell scripts like `sleep(20)`
