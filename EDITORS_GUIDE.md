# Zimfarm Editors Guide

This guide is intended for **editors** who manage recipes and monitor tasks on the Zimfarm platform. If you're looking for technical integration details, see [INTEGRATORS_GUIDE.md](INTEGRATORS_GUIDE.md).

## Table of Contents

- [What is Zimfarm?](#what-is-zimfarm)
- [Core Concepts](#core-concepts)
  - [Recipes](#recipes)
  - [Tasks](#tasks)
  - [Workers](#workers)
  - [Offliners (Scrapers)](#offliners-scrapers)
- [Task Assignment](#task-assignment)
  - [How Tasks Are Assigned](#how-tasks-are-assigned)
  - [Requested Tasks](#requested-tasks)

## What is Zimfarm?

Zimfarm is a distributed platform that automates the creation of [ZIM files](http://www.openzim.org/). The platform:

- allows the creation/modification of recipes
- creates tasks from a recipes
- assigns tasks to workers
- monitors task execution
- uploads ZIM files, logs, artifacts to the warehouse
- notifies users of task status

The Zimfarm web interface is available at [farm.openzim.org](https://farm.openzim.org/).

## Core Concepts

### Recipes

A **recipe** is a template for creating tasks which would be executed. It contains:

- **Name**: Unique identifier for the recipe (e.g., `wikipedia_en_all_maxi`)
- **Category**: Content type (e.g., `wikipedia`, `stack_exchange`, `ted`)
- **Offliner**: The scraper tool to use (e.g., `mwoffliner`, `youtube`, `zimit`).
- **Configuration**: Scraper-specific parameters and flags
- **Resources**: CPU, memory, and disk requirements of the recipe
- **Periodicity**: How often to create tasks for a recipe
- **Language**: ISO-6393 language code of the recipe.
- **Tags**: Labels for organization and filtering
- **Enabled/Disabled**: Whether tasks can be created from this recipe or not.
- **Archived**: Whether the recipe is archived or not. The archive is the equivalent of deleting a recipe.
- **Context**: Optional tag that a worker must have in order to be able to be eligible
  to work on tasks from the recipe. For example, a recipe with `vikidia` context
  will have it's tasks only executed by machines with the same `vikidia` context.

When a task is requested to be created from a recipe, an intermediary called "requested task" is created which contains
the current configurations of the recipe at a particular point in time. These requested tasks can be scheduled to run
on a specific worker machine or any available worker. When a worker signals it is available and the API deems the worker
to meet the resource constraints of the requested task, a task is created and the requested task is deleted.

### Tasks

A **task** is a single execution instance of a recipe. It is these tasks that produce ZIM files, logs and artifacts pertaining
to the execution. Tasks go through several states:

1. **Reserved**: Task has been assigned to a worker and is waiting to start.
2. **Started**: Worker has started executing the task. This does not mean the scraper is running as the scraper image needs to be pulled and environment needs to be setup.
3. **Scraper Started**: The scraper container has started.
4. **Scraper Running**: The scraper container is running.
5. **Scraper Completed**: The scraper container has stopped running. This does not mean tha the scraper run was successful.
6. **Succeeded/Failed**: For a task to be successful, the scraper run must be successful and all ZIM files produced must have been uploaded.
7. **Canceled**: Task was manually stopped either through a cancellation request or worker machine received signal to stop. Sometimes, stale tasks (tasks whose workers fail to respond over a period of time) are requested to be canceled by an automated script.

**NOTE**: A task can produce one or more ZIM files and depending on the content size,
a task can take between minutes and weeks to complete.

### Workers

**Workers** are computers that execute tasks. They:

- authenticate to the Zimfarm backend and request for tasks to be assigned to them.
- run scraper containers to process content.
- upload resulting ZIM files to the warehouse
- report progress and logs back to Zimfarm

**Worker Properties:**

- **Resources**: Available CPU, memory, and disk
- **Offliners**: Which scrapers they support
- **Platforms**: Limits on specific content types (e.g., max 2 YouTube tasks)
- **Selfish**: Only runs tasks specifically assigned to it
- **Cordoned**: Temporarily not accepting new tasks
- **Context**: Optional group of tags that allow a worker to run recipes with a context. In addition, each tag can have an IP address which allows the worker to be assigned
  a task only if it's last IP address matches the IP address of the tag. For example,
  if a worker with context `vikidia: 172.0.0.1` has last IP address of `172.0.0.2`,
  it will not be assigned recipes with `vikidia` context because it's last IP address
  does not match the IP address of the context.

These properties are taken into account by the algorithm that assigns a requested
task to a worker.

### Offliners (Scrapers)

**Offliners** are specialized tools that convert online content to ZIM format:

- **mwoffliner**: MediaWiki sites (Wikipedia, etc.)
- **youtube**: YouTube channels and playlists
- **zimit**: General websites (Warc2Zim-based)
- **sotoki**: Stack Exchange sites
- **gutenberg**: Project Gutenberg books
- **ted**: TED talks
- **phet**: PhET Interactive Simulations
- And many more...

[Check out OpenZIM's repositories](https://github.com/search?q=topic%3Ascraper+org%3Aopenzim&type=Repositories) for a complete list.

**NOTE**: Each offliner has specific configuration options relevant to its content type.
Always check the scraper documentation for available options while modifying the recipe from the UI.

## Task Assignment

### How Tasks Are Assigned

The Zimfarm uses a sophisticated algorithm to match tasks with workers. It considers
the following before assigning a "requested task" to a worker.

- Whether worker has sufficient **resources** (CPU, memory, disk)
- Whether worker supports the required **offliner**
- If worker hasn't exceeded **platform limits** (e.g., max 2 YouTube tasks)
- If worker's **context** matches recipe context and if **context** requires IP
  constraint, worker's last IP must match the **context**'s IP.
- If task is not already running on another worker
- If worker is selfish and only wants tasks explicitly assigned to them
- Sort tasks by priority (highest first), duration (longest first) and date task
  was requested at (oldest first).
- Check if worker can run the first task from this sorted list of requested tasks
- If worker can run the requested task, create a task and assign it to worker. Afterwards, the requested task is deleted.
- Otherwise:
  - Compute the currently running tasks if any that are hindering the requested task from running.
  - Determine the amount of time left for that task to complete
  - Determine the requested task that can be run within less than the completion time
    and still meets the resource constraints. Create a task from such requested task
    and delete the requested task.

### Requested Tasks

**Requested tasks** are tasks waiting for workers. View them at the [Todo Tab](https://farm.openzim.org/pipeline)
of the Zimfarm UI.

**Why tasks wait:**

- No worker with sufficient resources available
- No worker supports the required offliner
- Context requirement not met or IP restriction of the context is not satisified
- Higher priority tasks consuming all workers
- All workers cordoned or disabled
